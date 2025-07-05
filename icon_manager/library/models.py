import logging
import os
from typing import Iterable, Optional, Sequence, Tuple

from icon_manager.interfaces.path import (FileModel, Folder, FolderModel,
                                          JsonFile, PathModel)
from icon_manager.rules.manager import RuleManager

log = logging.getLogger(__name__)


class PngFile(FileModel):
    @ classmethod
    def _extension(cls) -> str:
        return 'png'


class JpgFile(FileModel):
    @ classmethod
    def _extension(cls) -> str:
        return 'jpg'


class JpegFile(FileModel):
    @ classmethod
    def _extension(cls) -> str:
        return 'jpeg'


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

    def __init__(self, icon: LibraryIconFile, manager: RuleManager) -> None:
        self.icon = icon
        self.manager = manager

    @property
    def name(self) -> str:
        return self.icon.name_wo_extension

    @property
    def order_key(self) -> Tuple[str, str]:
        weight = f'{self.manager.weight:02d}'
        return (weight, self.manager.name)

    @property
    def copy_icon(self) -> Optional[bool]:
        return self.manager.copy_icon

    def archive_files(self) -> Sequence[FileModel]:
        name = self.icon.name_wo_extension
        files = [
            self.icon, self.manager.config,
            PngFile(self.icon.sibling_path(f'{name}{PngFile.extension()}')),
            JpgFile(self.icon.sibling_path(f'{name}{JpgFile.extension()}')),
            JpegFile(self.icon.sibling_path(f'{name}{JpegFile.extension()}'))
        ]
        return [file for file in files if file.exists()]

    def is_config_for(self, entry: Folder) -> bool:
        return self.manager.is_allowed(entry)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        self.manager.setup_rules(before_or_after)

    def is_empty(self) -> bool:
        return self.manager.is_empty()

    def __str__(self) -> str:
        return f'Icon Setting: {self.icon.name_wo_extension}'

    def __repr__(self) -> str:
        return self.__str__()


class ArchiveFile(FileModel):
    pass


class ArchiveFolder(FolderModel):

    folder_name: str = '__archive__'

    @ classmethod
    def get_archive_folder(cls, entry: PathModel) -> 'ArchiveFolder':
        """
        Return an ArchiveFolder instance representing the archive folder associated with the given entry.
        
        If the entry is a directory, the archive folder is created inside that directory. Otherwise, it is created inside the parent directory of the entry.
        
        Parameters:
            entry (PathModel): The file or directory for which to determine the archive folder location.
        
        Returns:
            ArchiveFolder: An instance representing the resolved archive folder path.
        """
        if entry.is_dir():
            return ArchiveFolder(os.path.join(entry.path, cls.folder_name))
        return ArchiveFolder(os.path.join(entry.parent_path, cls.folder_name))

    @ classmethod
    def is_model(cls, path: str) -> bool:
        """
        Return True if the given path ends with the archive folder name.
        
        Parameters:
            path (str): The file system path to check.
        
        Returns:
            bool: True if the path ends with the archive folder name, otherwise False.
        """
        return path.endswith(cls.folder_name)

    def get_archive_path(self, model: FileModel) -> str:
        return os.path.join(self.path, model.name)

    def get_archive_file(self, file: FileModel) -> ArchiveFile:
        """
        Return an ArchiveFile instance representing the given file's path within the archive folder.
        
        Parameters:
        	file (FileModel): The file to be archived.
        
        Returns:
        	ArchiveFile: The archive file corresponding to the input file within the archive folder.
        """
        archive_path = self.get_archive_path(file)
        return ArchiveFile(archive_path)

    def is_archive(self, path: str) -> bool:
        """
        Return True if the given path is within this archive folder.
        
        Parameters:
            path (str): The path to check.
        
        Returns:
            bool: True if the path starts with the archive folder's path, otherwise False.
        """
        return path.startswith(self.path)
