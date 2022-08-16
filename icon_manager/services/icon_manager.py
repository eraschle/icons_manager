import logging
from typing import Optional

from icon_manager.config.config import AppConfig
from icon_manager.controller.config import (AppConfigController,
                                            LocalConfigController)
from icon_manager.controller.folder import IconFolderController
from icon_manager.controller.icons import IconsController
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.resource import app_config_and_template
from icon_manager.helpers.string import HUNDRED, PREFIX_LENGTH, fixed_length
from icon_manager.managers.desktop import DesktopFileManager
from icon_manager.models.path import JsonFile

log = logging.getLogger(__name__)


class IconFolderService:

    def __init__(self, config: AppConfig,
                 manager: DesktopFileManager = DesktopFileManager()) -> None:
        self.config = config
        self.manager = manager
        self.icons_ctrl = IconsController(config)
        self.folders_ctrl = IconFolderController(manager)

    def delete_icon_folder_configs(self):
        for path in self.config.folders.get_search_folder_paths():
            controller = LocalConfigController(path)
            folders, files = controller.delete_existing_configs(self.manager)
            files_count = fixed_length(str(len(files)), HUNDRED)
            folders_count = fixed_length(str(len(folders)), HUNDRED)
            prefix = fixed_length("Deleted Files:", PREFIX_LENGTH, align='<')
            message = f'{prefix}{files_count} Folders: {folders_count} in {controller.full_path}'
            log.info(message)

    def add_icons_to_folders(self, overwrite: bool):
        self.icons_ctrl.create_icon_config(remove_empty=True)
        self.folders_ctrl.icon_configs = self.icons_ctrl.icon_configs
        for folder_path in self.config.search_folder_paths():
            start = len(self.folders_ctrl.icon_folders)
            self.folders_ctrl.add_icon_folders(folder_path, overwrite)
            amount = len(self.folders_ctrl.icon_folders) - start
            amount = fixed_length(str(amount), HUNDRED)
            prefix = fixed_length("Added Config:", PREFIX_LENGTH, align='<')
            log.info(f'{prefix}{amount} in {folder_path}')

    def re_write_icon_config(self):
        self.icons_ctrl.create_icon_config(remove_empty=True)
        self.folders_ctrl.icon_configs = self.icons_ctrl.icon_configs
        for folder_path in self.config.search_folder_paths():
            controller = LocalConfigController(folder_path)
            local_folders = controller.get_existing_local_folders()
            self.folders_ctrl.re_write_config_file(local_folders, folder_path)

    def create_icon_config_templates(self, overwrite: bool, update: bool) -> None:
        if update:
            self.icons_ctrl.update_icon_config_files()
        else:
            self.icons_ctrl.create_icon_config_files(overwrite)

    def archive_empty_icon_configs(self):
        self.icons_ctrl.create_icon_config(remove_empty=False)
        self.icons_ctrl.archive_empty_icon_configs()

# region START AND LOAD APP


DEVELOP = True


def ask_user_export_path() -> str:
    return input("Enter path for loading config: ")


def ask_user_config_not_exist(config: AppConfig) -> str:
    message = "Saved config file path does not exists: Change y / n: "
    answer = input(message)
    if answer in ('y', 'Y', 'j', 'J'):
        return ask_user_export_path()
    path = config.get_user_app_config_path()
    if path is None:
        raise RuntimeError('Should not be possible')
    return path


def get_app_config(config_file: JsonFile) -> AppConfig:
    config = AppConfig(config_file)
    config.read_config(JsonSource())
    config.validate()
    return config


def ask_user_about_export(config_file: Optional[JsonFile], config: AppConfig):
    if config_file is None:
        return ask_user_export_path()
    return ask_user_config_not_exist(config)


def export_user_config(config_path: str, config: AppConfig) -> JsonFile:
    controller = AppConfigController(config_path, config)
    config_file = controller.get_or_create_user_config()
    controller.export_user_app_config(config_file, DEVELOP)
    return config_file


def get_user_config(config: AppConfig) -> AppConfig:
    config_file = config.get_user_app_config_file()
    if config_file is None or not config_file.exists():
        config_path = ask_user_about_export(config_file, config)
        config_file = export_user_config(config_path, config)
    return get_app_config(config_file)


def get_service() -> IconFolderService:
    config_file = app_config_and_template()
    app_config = get_app_config(config_file)
    user_config = get_user_config(app_config)
    service = IconFolderService(user_config)
    return service


# endregion
