import logging
import os
from typing import Iterable, List, Optional, Tuple

from icon_manager.config.config import AppConfig
from icon_manager.controller.base import FileBaseController
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.resource import app_config_and_template
from icon_manager.managers.desktop import DesktopFileManager
from icon_manager.managers.find import File, FindOptions, Folder
from icon_manager.models.path import (DesktopIniFile, FileModel, FolderModel,
                                      JsonFile, LocalIconFolder)

log = logging.getLogger(__name__)


class AppConfigController(FileBaseController[JsonFile]):

    config_file_name = 'config.json'

    def __init__(self, full_path: str, config: AppConfig) -> None:
        super().__init__(full_path, JsonFile)
        self.config = config
        self.source = JsonSource()

    def get_or_create_user_config_file(self) -> JsonFile:
        path = self.full_path
        name = AppConfigController.config_file_name
        if self.full_path.endswith(JsonFile.extension()):
            name = os.path.basename(self.full_path)
            path = os.path.dirname(self.full_path)
            folder = FolderModel(path)
            if not folder.exists():
                folder.create()
        file_path = os.path.join(path, name)
        return JsonFile(file_path)

    def get_or_create_user_config(self) -> JsonFile:
        app_file = app_config_and_template()
        user_file = self.config.get_user_app_config_file()
        if user_file is None or not user_file.exists():
            user_file = self.get_or_create_user_config_file()
            config = self.config.get_app_config_with_user(user_file)
            self.source.write(app_file, config)
        return user_file

    def export_user_app_config(self, config_file: JsonFile, develop: bool) -> None:
        user_config = self.config.get_user_config_template(develop)
        self.source.write(config_file, user_config)


class LocalConfigController(FileBaseController[DesktopIniFile]):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path, DesktopIniFile)
        self.icon_folders: List[LocalIconFolder] = []

    def get_find_options(self) -> FindOptions:
        options = super().get_find_options()
        options.add_folder_allowed(LocalIconFolder.is_model)
        options.clear_stop_recursive()
        return options

    def get_icon_folder(self, folders: Iterable[Folder]) -> Optional[LocalIconFolder]:
        for folder in folders:
            if not LocalIconFolder.is_model(folder.full_path):
                continue
            return LocalIconFolder(folder.full_path)
        return None

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        super().on_found_folders_and_files(folders, files)
        self.icon_folders.extend(self.create_folders(folders))

    def create_folders(self, folders: Iterable[Folder]) -> Iterable[LocalIconFolder]:
        return [LocalIconFolder(folder.full_path) for folder in folders]

    def get_file(self, folders: Iterable[Folder], file: File) -> DesktopIniFile:
        folder = self.get_icon_folder(folders)
        return self.file_type(file.full_path, folder)

    def create_files(self, folders: Iterable[Folder], files: Iterable[File]) -> Iterable[DesktopIniFile]:
        return [self.get_file(folders, file) for file in files]

    def delete_existing_configs(self, manager: DesktopFileManager) -> Tuple[List[FolderModel], List[FileModel]]:
        folders, files = self.delete_existing_files(manager)
        folders.extend(self.delete_existing_folders())
        return folders, files

    def delete_existing_files(self, manager: DesktopFileManager) -> Tuple[List[FolderModel], List[FileModel]]:
        folders: List[FolderModel] = []
        files: List[FileModel] = []
        for file in self.get_files():
            folder = file.icon_folder
            if folder is not None:
                folder.remove()
                folders.append(folder)
            if not manager.can_delete_config(file):
                log.warning(f'Can not delete "{file.path}"')
            file.remove()
            files.append(file)
        return folders, files

    def delete_existing_folders(self) -> Iterable[FolderModel]:
        folders: List[FolderModel] = []
        for folder in self.icon_folders:
            if not folder.exists():
                continue
            folder.remove()
            folders.append(folder)
        return folders
