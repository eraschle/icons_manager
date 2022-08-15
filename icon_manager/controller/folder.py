from typing import Iterable, List, Optional

from icon_manager.controller.base import BaseController
from icon_manager.models.config import IconConfig
from icon_manager.models.container import IconContainer
from icon_manager.models.path import (DesktopIniFile, FolderModel,
                                      LocalIconFolder)
from icon_manager.tasks.find_folders import File, FindOptions, Folder
from icon_manager.utils.path import get_files


class IconFolderController(BaseController):

    def __init__(self) -> None:
        super().__init__()
        self.icon_configs: Iterable[IconConfig] = []
        self.icon_folders: List[IconContainer] = []

    def get_find_options(self) -> FindOptions:
        options = FindOptions(add_default=True,
                              folder_excluded=LocalIconFolder.is_model,
                              file_allowed=FindOptions.no_file_allowed)
        return options

    def collect_icon_folders(self, full_path: str, overwrite: bool) -> None:
        self.overwrite = overwrite
        self.search_for_folders_and_files(full_path, search_again=True)

    def create_folders(self, folders: Iterable[Folder], _: Iterable[File]) -> Iterable[FolderModel]:
        return [FolderModel(folder.full_path) for folder in folders]

    def config_exists_already(self, folder: FolderModel) -> bool:
        files = get_files(folder.path)
        return DesktopIniFile.file_name in files

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        folder_models = self.create_folders(folders, files)
        for folder in folder_models:
            if not self.overwrite and self.config_exists_already(folder):
                continue
            icon_folder = self.get_icon_folder(folder)
            if icon_folder is None:
                continue
            print(f'Added {folder.name} >> {icon_folder.icon_file.name}')
            self.icon_folders.append(icon_folder)

    def get_icon_folder(self, folder: FolderModel) -> Optional[IconContainer]:
        config = self.icon_config_for(folder)
        if config is None:
            return None
        return IconContainer(folder, config)

    def icon_config_for(self, folder: FolderModel) -> Optional[IconConfig]:
        for config in self.icon_configs:
            if not config.is_config_for(folder):
                continue
            return config
        return None
