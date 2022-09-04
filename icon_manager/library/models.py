import logging
import os
from typing import Iterable, Tuple

from icon_manager.helpers.path import Folder
from icon_manager.interfaces.path import (FileModel, FolderModel, JsonFile,
                                          PathModel)
from icon_manager.rules.config import RuleConfig

log = logging.getLogger(__name__)


class IconFile(FileModel):

    @ classmethod
    def _extension(cls) -> str:
        return 'ico'


class LibraryIconFile(IconFile):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path)
        self.__config = self.__create_config()

    def get_config(self) -> JsonFile:
        return self.__config

    def __create_config(self) -> JsonFile:
        file_name = self.name_wo_extension
        file_name = f'{file_name}{JsonFile.extension()}'
        file_path = self.path.replace(self.name, file_name)
        return JsonFile(file_path)


class IconSetting:

    def __init__(self, icon: LibraryIconFile, config: RuleConfig) -> None:
        self.icon = icon
        self.rule_config = config

    @property
    def name(self) -> str:
        return self.icon.name_wo_extension

    @property
    def order_key(self) -> Tuple[str, str]:
        weight = f'{self.rule_config.order_weight:02d}'
        return (weight, self.icon.name)

    def is_config_for(self, entry: Folder) -> bool:
        return self.rule_config.is_config_for(entry)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        self.rule_config.set_before_or_after(before_or_after)

    def is_empty(self) -> bool:
        return self.rule_config.is_empty()

    def __str__(self) -> str:
        return f'Icon Setting: {self.icon.name_wo_extension}'

    def __repr__(self) -> str:
        return self.__str__()


class ArchiveFile(FileModel):
    pass


class ArchiveFolder(FolderModel):

    folder_name: str = '__archive__'

    @ classmethod
    def get_folder_path(cls, entry: PathModel) -> str:
        if entry.is_dir():
            return os.path.join(entry.name, cls.folder_name)
        return os.path.join(entry.parent_path, cls.folder_name)

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.folder_name)

    def get_archive_path(self, model: FileModel) -> str:
        return os.path.join(self.path, model.name)

    def get_archive_file(self, file: FileModel) -> ArchiveFile:
        archive_path = self.get_archive_path(file)
        return ArchiveFile(archive_path)
