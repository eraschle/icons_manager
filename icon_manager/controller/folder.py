import logging
import os
from typing import Collection, Iterable, List, Optional

from icon_manager.controller.base import BaseController
from icon_manager.helpers.path import get_files
from icon_manager.helpers.string import HUNDRED, PREFIX_LENGTH, fixed_length
from icon_manager.managers.desktop import DesktopFileManager
from icon_manager.managers.find import File, FindOptions, Folder
from icon_manager.managers.icon_folder import IconFolderManager
from icon_manager.models.config import IconConfig
from icon_manager.models.path import FolderModel, IconFile, LocalIconFolder

log = logging.getLogger(__name__)


class IconFolderController(BaseController):

    def __init__(self, manager: DesktopFileManager) -> None:
        super().__init__()
        self.manager = manager
        self.icon_configs: Iterable[IconConfig] = []
        self.icon_folders: List[IconFolderManager] = []

    def get_find_options(self) -> FindOptions:
        options = FindOptions(add_default=True,
                              folder_excluded=LocalIconFolder.is_model,
                              file_allowed=FindOptions.no_file_allowed)
        return options


# region WRITE CONFIG FILES


    def add_icon_folders(self, full_path: str, overwrite: bool) -> None:
        self.overwrite = overwrite
        self.search_for_folders_and_files(full_path, search_again=True)

    def create_folders(self, folders: Iterable[Folder], _: Iterable[File]) -> Iterable[FolderModel]:
        return [FolderModel(folder.full_path) for folder in folders]

    def can_write(self, folder: IconFolderManager) -> bool:
        if not folder.ini_file.exists():
            return True
        can_write = self.manager.can_write_config(folder.ini_file)
        if not can_write:
            log.warning(f'Can not write desktop.ini in "{folder.path}"')
        return can_write and self.overwrite

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        folder_models = self.create_folders(folders, files)
        for folder in folder_models:
            icon_folder = self.get_icon_config_for(folder)
            if icon_folder is None or not self.can_write(icon_folder):
                continue
            if not self.manager.write_config(icon_folder):
                continue
            message = f'Write icon config "{icon_folder.icon_file.name}" to "{folder.path}"'
            log.debug(message)
            self.icon_folders.append(icon_folder)

    def get_icon_config_for(self, folder: FolderModel) -> Optional[IconFolderManager]:
        config = self.icon_config_for(folder)
        if config is None:
            return None
        return IconFolderManager(folder, config)


# endregion


# region RE WRITE CONFIG FILES


    def icon_config_for(self, folder: FolderModel) -> Optional[IconConfig]:
        for config in self.icon_configs:
            if not config.is_config_for(folder):
                continue
            return config
        return None

    def icon_file_by(self, local_folder: LocalIconFolder) -> Optional[IconFile]:
        for file_name in get_files(local_folder.path):
            if not IconFile.is_model(file_name):
                continue
            file_path = os.path.join(local_folder.path, file_name)
            return IconFile(file_path)
        return None

    def icon_config_by(self, icon_file: IconFile) -> Optional[IconConfig]:
        for config in self.icon_configs:
            if config.icon_file.name != icon_file.name:
                continue
            return config
        return None

    def get_icon_config_by(self, local_folder: LocalIconFolder) -> Optional[IconConfig]:
        icon_file = self.icon_file_by(local_folder)
        if icon_file is None:
            return None
        return self.icon_config_by(icon_file)

    def get_icon_folder(self, local_folder: LocalIconFolder) -> Optional[IconFolderManager]:
        icon_config = self.get_icon_config_by(local_folder)
        if icon_config is None:
            return None
        folder = local_folder.parent_folder()
        return IconFolderManager(folder, icon_config)

    def re_write_config_file(self, local_folders: Collection[LocalIconFolder], folder_path: str):
        re_written_files = []
        for folder in local_folders:
            icon_folder = self.get_icon_folder(folder)
            if icon_folder is None:
                continue
            if not self.manager.write_config(icon_folder):
                continue
            re_written_files.append(icon_folder)

        folders = fixed_length(str(len(local_folders)), HUNDRED)
        files = fixed_length(str(len(re_written_files)), HUNDRED)

        prefix = fixed_length("Re written config:", PREFIX_LENGTH, align='<')
        log.info(f'{prefix} Files: {files} of {folders} in {folder_path}')


# endregion
