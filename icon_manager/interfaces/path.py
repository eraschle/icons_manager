import logging
import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional
from uuid import UUID, uuid4

log = logging.getLogger(__name__)

log = logging.getLogger(__name__)


@dataclass
class Node:
    name: str = field(repr=True)
    parent_name: str = field(repr=True)
    path: str = field(compare=True, hash=True, repr=False)
    excluded: bool

    def is_file(self) -> bool:
        return os.path.isfile(self.path)

    def is_dir(self) -> bool:
        return os.path.isdir(self.path)


@dataclass()
class File(Node):
    name_wo_ext: str
    ext: Optional[str]


@dataclass()
class Folder(Node):
    folders: List['Folder'] = field(default_factory=list)
    files: List[File] = field(default_factory=list)

    def mark_children_excluded(self) -> None:
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


def get_attr_bit_dict(attributes: Iterable[str], is_enable: bool) -> Dict[str, str]:
    attr_dict = {}
    for attribute in attributes:
        value = '+' if is_enable else '-'
        attr_dict[attribute] = value
    return attr_dict


class PathModel(ABC):

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return False

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def escape_path(self) -> str:
        if ' ' not in self.path:
            return self.path
        return f'"{self.path}"'

    @property
    def parent_path(self) -> str:
        head, _ = os.path.split(self.path)
        if head is None or len(head) == 0:
            return os.path.dirname(self.path)
        return head

    @abstractmethod
    def child_path(self, child_name: str) -> str:
        ...

    def sibling_path(self, entry_name: str) -> str:
        return os.path.join(self.parent_path, entry_name)

    def exists(self) -> bool:
        return self.is_file() or self.is_dir()

    @abstractmethod
    def is_file(self) -> bool:
        ...

    @abstractmethod
    def is_dir(self) -> bool:
        ...

    def __command(self, attributes: Dict[str, str]) -> str:
        commands = ['attrib']
        for attr, value in attributes.items():
            commands.append(f'{value}{attr}')
        commands.append(self.escape_path)
        return ' '.join(commands)

    def set_attrib(self, attributes: Dict[str, str]) -> None:
        command = self.__command(attributes)
        os.system(command)

    def set_read_only(self, is_read_only: bool) -> None:
        attr_dict = get_attr_bit_dict(['r'], is_read_only)
        self.set_attrib(attr_dict)

    def set_hidden(self, is_hidden: bool) -> None:
        attr_dict = get_attr_bit_dict(['s', 'h'], is_hidden)
        self.set_attrib(attr_dict)

    def remove(self) -> None:
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
            else:
                shutil.rmtree(self.path, ignore_errors=False)
        except Exception as ex:
            message = f'Can not delete {self.name} in {self.parent_path}'
            log.exception(message, ex)

    def copy_to(self, destination):
        if not isinstance(destination, PathModel):
            message = f'Expected  PathModel but got {type(destination)}'
            raise AttributeError(message)
        shutil.copy(self.path, destination.path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PathModel):
            return False
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    def __str__(self) -> str:
        return f'{self.name} [{self.parent_path}]'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {self.__str__()}'


class FileModel(PathModel):

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.extension())

    @ classmethod
    def extension(cls, with_point: bool = True) -> str:
        if with_point:
            return f'.{cls._extension()}'
        return cls._extension()

    @ classmethod
    def _extension(cls) -> str:
        raise NotImplementedError

    def __init__(self, path: str) -> None:
        super().__init__(path)

    @ property
    def name_wo_extension(self) -> str:
        extension = self.__class__.extension()
        return self.name.replace(extension, '')

    def child_path(self, child_name: str) -> str:
        path = self.parent_path
        return os.path.join(path, child_name)

    def is_file(self) -> bool:
        return os.path.exists(self.path)

    def is_dir(self) -> bool:
        return False


class JsonFile(FileModel):

    @ classmethod
    def _extension(cls) -> str:
        return 'json'


class ConfigFile(JsonFile):

    @ classmethod
    def _extension(cls) -> str:
        return 'config'


class FolderModel(PathModel):

    @ classmethod
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
    def __init__(self, path: str, copy_icon: Optional[bool]) -> None:
        super().__init__(path)
        self.copy_icon = copy_icon
