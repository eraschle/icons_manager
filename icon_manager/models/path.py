import os
import shutil
from abc import ABC
from typing import Dict, Iterable, Optional


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

    def __init__(self, full_path: str) -> None:
        super().__init__()
        self.__full_path = full_path

    def exists(self) -> bool:
        return os.path.isfile(self.path) or os.path.isdir(self.path)

    @property
    def path(self) -> str:
        return self.__full_path

    @property
    def escape_path(self) -> str:
        if ' ' not in self.__full_path:
            return self.__full_path
        return f'"{self.__full_path}"'

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

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

    def remove(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
        else:
            shutil.rmtree(self.path, ignore_errors=False)

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
        return f'PATH: {self.name}'

    def __repr__(self) -> str:
        return self.__str__()


class FolderModel(PathModel, ABC):

    def create(self):
        os.makedirs(self.path, exist_ok=True)

    def __str__(self) -> str:
        return f'Folder: {self.name}'


class FileModel(PathModel, ABC):

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.extension())

    @ classmethod
    def extension(cls) -> str:
        raise NotImplementedError

    @ property
    def name_wo_extension(self) -> str:
        extension = f'.{self.__class__.extension()}'
        return self.name.replace(extension, '')

    def __str__(self) -> str:
        return f'File: {self.name_wo_extension}'

    def __repr__(self) -> str:
        return f'{self.__str__()} [{self.__class__.extension()}]'


class JsonFile(FileModel):

    @ classmethod
    def extension(cls) -> str:
        return 'json'


class IconFile(FileModel):

    @ classmethod
    def extension(cls) -> str:
        return 'ico'


class LocalIconFolder(FolderModel):

    folder_name: str = '__icon__'

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.folder_name)

    def parent_folder(self) -> FolderModel:
        parent_path = os.path.dirname(self.path)
        return FolderModel(parent_path)


class DesktopIniFile(FileModel):

    file_name = 'desktop.ini'

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.file_name)

    @ classmethod
    def extension(cls) -> str:
        return 'ini'

    def __init__(self, full_path: str, icon_folder: Optional[LocalIconFolder] = None) -> None:
        super().__init__(full_path)
        self.icon_folder = icon_folder

    def set_protected_and_hidden(self) -> None:
        self.set_attrib({'s': '+', 'h': '+'})

    def set_writeable_and_visible(self) -> None:
        self.set_attrib({'s': '-', 'h': '-'})
