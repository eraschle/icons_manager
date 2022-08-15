import logging
import os

from icon_manager.models.config import IconConfig
from icon_manager.models.path import (DesktopIniFile, FolderModel, IconFile,
                                      LocalIconFolder)

log = logging.getLogger(__name__)


class IconFolderHandler(FolderModel):
    def __init__(self, folder: FolderModel, config: IconConfig) -> None:
        super().__init__(folder.path)
        self.ini_file = self.create_desktop_ini()
        self.config = config

    @property
    def icon_file(self) -> IconFile:
        return self.config.icon_file

    def create_desktop_ini(self) -> DesktopIniFile:
        path = os.path.join(self.path, DesktopIniFile.file_name)
        return DesktopIniFile(path)

    def config_icon_path(self) -> str:
        icon_path = self.config.icon_file.path
        if not self.config.copy_icon:
            return icon_path
        return os.path.relpath(icon_path, self.path)

    def copy_icon_to_local_folder(self) -> IconFile:
        copy_file = self.local_icon_file()
        if copy_file.exists():
            copy_file.remove()
        self.config.icon_file.copy_to(copy_file)
        return copy_file

    def create_icon_folder(self) -> LocalIconFolder:
        path = os.path.join(self.path, LocalIconFolder.folder_name)
        return LocalIconFolder(path)

    def local_icon_folder(self) -> LocalIconFolder:
        folder = self.create_icon_folder()
        if not folder.exists():
            folder.create()
        return folder

    def local_icon_file(self) -> IconFile:
        local_folder = self.local_icon_folder()
        icon_name = self.config.icon_file.name
        path = os.path.join(local_folder.path, icon_name)
        return IconFile(path)

    def __str__(self) -> str:
        return f'{self.name} [{self.config}]'

    def __repr__(self) -> str:
        return self.__str__()
