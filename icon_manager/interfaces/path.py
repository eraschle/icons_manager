import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from uuid import uuid4

log = logging.getLogger(__name__)


def get_parent_and_name(path: str) -> tuple[str, str]:
    return os.path.split(path)


_POINT = "."


def get_name_and_extension(path: str) -> tuple[str, str | None]:
    _, name = get_parent_and_name(path)
    if _POINT not in name or name.startswith(_POINT):
        return name, None
    splitted = name.split(_POINT)
    return ".".join(splitted[:-1]), splitted[-1]


@dataclass
class Node:
    parent: "Folder | None"
    path: str
    name: str = field(init=False)
    excluded: bool = field(default=False, init=False)

    def __post_init__(self):
        _, name = get_parent_and_name(self.path)
        self.name = name

    @property
    def parent_path(self) -> str:
        if self.parent is not None:
            return self.parent.path
        parent, name = os.path.split(self.path)
        if parent is None or len(parent) == 0:
            return name
        return parent

    @property
    def parent_name(self) -> str:
        if self.parent is not None:
            return self.parent.name
        _, name = os.path.split(self.parent_path)
        return name

    def is_file(self) -> bool:
        return os.path.isfile(self.path)

    def is_dir(self) -> bool:
        return os.path.isdir(self.path)

    def exists(self) -> bool:
        return os.path.exists(self.path)


@dataclass()
class File(Node):
    name_wo_ext: str = field(init=False)
    ext: str | None = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        name_wo_ext, ext = get_name_and_extension(self.name)
        self.name_wo_ext = name_wo_ext
        self.ext = ext

    @classmethod
    def from_path(cls, path: str, parent: "Folder | None") -> "File":
        return File(parent=parent, path=path)


@dataclass()
class Folder(Node):
    folders: list["Folder"] = field(default_factory=list)
    files: list[File] = field(default_factory=list)

    @classmethod
    def from_path(cls, path: str, parent: "Folder | None") -> "Folder":
        return Folder(parent=parent, path=path)

    def mark_children(self) -> None:
        for folder in self.folders:
            folder.excluded = True
        for file in self.files:
            file.excluded = True

    def mark_and_clean(self) -> None:
        self.excluded = True
        for folder in self.folders:
            folder.excluded = True
        self.folders.clear()
        for file in self.files:
            file.excluded = True
        self.files.clear()


def is_file(path: str, name: str, extension: str | None = None) -> bool:
    """Whether ``name`` in ``path`` is a file, optionally of ``extension``."""
    if not os.path.isfile(os.path.join(path, name)):
        return False
    if extension is None:
        return True
    if not extension.startswith("."):
        extension = f".{extension}"
    return name.endswith(extension)


def get_files(path: str, extension: str | None = None) -> list[str]:
    """The file names directly in ``path``, optionally filtered by extension."""
    return [name for name in os.listdir(path) if is_file(path, name, extension)]


def get_attr_bit_dict(attributes: Iterable[str], is_enable: bool) -> dict[str, str]:
    attr_dict = {}
    for attribute in attributes:
        value = "+" if is_enable else "-"
        attr_dict[attribute] = value
    return attr_dict


class PathModel(ABC):
    """A single path plus the operations that touch the disk for it.

    The counterpart to the Node/File/Folder dataclasses: those hold a crawl
    result, this acts on one path.
    """

    @classmethod
    @abstractmethod
    def is_model(cls, path: str) -> bool:
        """Whether ``path`` is one of these.

        Was a concrete ``return False`` on this base, so a subclass that
        forgot to override it silently matched nothing.
        """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def parent_path(self) -> str:
        head, _ = os.path.split(self.path)
        if head is None or len(head) == 0:
            return os.path.dirname(self.path)
        return head

    @abstractmethod
    def child_path(self, child_name: str) -> str: ...

    def sibling_path(self, entry_name: str) -> str:
        return os.path.join(self.parent_path, entry_name)

    def exists(self) -> bool:
        return self.is_file() or self.is_dir()

    @abstractmethod
    def is_file(self) -> bool: ...

    @abstractmethod
    def is_dir(self) -> bool: ...

    def set_attrib(self, attributes: dict[str, str]) -> None:
        """Set Windows file attributes, e.g. ``{"h": "+"}`` to hide the entry.

        Windows only; elsewhere attrib does not exist and the call is a
        logged no-op, which is what lets the rest of the tool be tested off
        Windows.

        Passed to subprocess as an argument list rather than to os.system as
        a string: the path went through the shell before, so a folder whose
        name contained shell metacharacters was interpreted rather than
        quoted, and a failure was silently discarded along with the exit
        code.
        """
        command = ["attrib", *(f"{value}{attr}" for attr, value in attributes.items()), self.path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except (FileNotFoundError, OSError) as ex:
            log.debug("attrib is unavailable, cannot set %s on %s: %s", attributes, self.path, ex)
            return
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            log.warning("attrib %s failed for %s: %s", attributes, self.path, message)

    def set_read_only(self, is_read_only: bool) -> None:
        attr_dict = get_attr_bit_dict(["r"], is_read_only)
        self.set_attrib(attr_dict)

    def set_hidden(self, is_hidden: bool) -> None:
        attr_dict = get_attr_bit_dict(["s", "h"], is_hidden)
        self.set_attrib(attr_dict)

    def remove(self) -> None:
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
            else:
                shutil.rmtree(self.path, ignore_errors=False)
        except OSError:
            log.exception("Can not delete %s in %s", self.name, self.parent_path)

    def copy_to(self, destination):
        if not isinstance(destination, PathModel):
            message = f"Expected  PathModel but got {type(destination)}"
            raise AttributeError(message)
        shutil.copy(self.path, destination.path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PathModel):
            return False
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    def __str__(self) -> str:
        return f"{self.name} [{self.parent_path}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.__str__()}"


class FileModel(PathModel):
    @classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.extension())

    @classmethod
    def extension(cls, with_point: bool = True) -> str:
        if with_point:
            return f".{cls._extension()}"
        return cls._extension()

    @classmethod
    @abstractmethod
    def _extension(cls) -> str:
        """The extension without its dot, e.g. ``"json"``."""

    def __init__(self, path: str) -> None:
        super().__init__(path)

    @property
    def name_wo_extension(self) -> str:
        extension = self.__class__.extension()
        return self.name.replace(extension, "")

    def child_path(self, child_name: str) -> str:
        path = self.parent_path
        return os.path.join(path, child_name)

    def is_file(self) -> bool:
        return os.path.exists(self.path)

    def is_dir(self) -> bool:
        return False


class JsonFile(FileModel):
    @classmethod
    def _extension(cls) -> str:
        return "json"


class ConfigFile(JsonFile):
    @classmethod
    def _extension(cls) -> str:
        return "config"


class FolderModel(PathModel):
    @classmethod
    def is_model(cls, path: str) -> bool:
        return os.path.isdir(path)

    def __init__(self, path: str) -> None:
        super().__init__(path)

    def child_path(self, child_name: str) -> str:
        path = self.path
        return os.path.join(path, child_name)

    def is_file(self) -> bool:
        return False

    def is_dir(self) -> bool:
        return os.path.exists(self.path)

    def create(self):
        os.makedirs(self.path, exist_ok=True)


class SearchFolder(FolderModel):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.uuid = uuid4()

    def is_path_entry(self, entry: PathModel) -> bool:
        return entry.path.startswith(self.path)


class IconSearchFolder(SearchFolder):
    def __init__(self, path: str, copy_icon: bool | None) -> None:
        super().__init__(path)
        self.copy_icon = copy_icon
