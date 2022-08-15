import logging
from typing import Iterable, List, Optional

from icon_manager.controller.base import BaseController
from icon_manager.handler.desktop_ini import DesktopIniManager
from icon_manager.handler.icon_config import IconFolderHandler
from icon_manager.models.config import IconConfig
from icon_manager.models.path import FolderModel, LocalIconFolder
from icon_manager.tasks.find_folders import File, FindOptions, Folder

log = logging.getLogger(__name__)


class IconFolderController(BaseController):

    def __init__(self, manager: DesktopIniManager) -> None:
        super().__init__()
        self.manager = manager
        self.icon_configs: Iterable[IconConfig] = []
        self.icon_folders: List[IconFolderHandler] = []

    def get_find_options(self) -> FindOptions:
        options = FindOptions(add_default=True,
                              folder_excluded=LocalIconFolder.is_model,
                              file_allowed=FindOptions.no_file_allowed)
        return options

    def add_icon_folders(self, full_path: str, overwrite: bool) -> None:
        self.overwrite = overwrite
        self.search_for_folders_and_files(full_path, search_again=True)

    def create_folders(self, folders: Iterable[Folder], _: Iterable[File]) -> Iterable[FolderModel]:
        return [FolderModel(folder.full_path) for folder in folders]

    def can_write(self, folder: IconFolderHandler) -> bool:
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
            self.manager.write_config(icon_folder)
            message = f'Added icon "{icon_folder.icon_file.name}" to "{folder.path}"'
            log.debug(message)
            self.icon_folders.append(icon_folder)

    def get_icon_config_for(self, folder: FolderModel) -> Optional[IconFolderHandler]:
        config = self.icon_config_for(folder)
        if config is None:
            return None
        return IconFolderHandler(folder, config)

    def icon_config_for(self, folder: FolderModel) -> Optional[IconConfig]:
        for config in self.icon_configs:
            if not config.is_config_for(folder):
                continue
            return config
        return None
