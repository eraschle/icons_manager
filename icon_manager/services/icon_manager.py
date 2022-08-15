import logging

from icon_manager.config.config import AppConfig
from icon_manager.controller.config import LocalConfigController
from icon_manager.controller.config_app import AppConfigController
from icon_manager.controller.folder import IconFolderController
from icon_manager.controller.icons import IconsController
from icon_manager.handler.desktop_ini import DesktopIniManager

log = logging.getLogger(__name__)


class IconFolderService:
    def __init__(self, config: AppConfig,
                 manager: DesktopIniManager = DesktopIniManager()) -> None:
        self.config = config
        self.manager = manager
        self.icons_ctrl = IconsController(config)
        self.folders_ctrl = IconFolderController(manager)

    def read_config(self):
        self.icons_ctrl.create_icon_config()

    def delete_icon_folder_configs(self):
        for path in self.config.folders.get_search_folder_paths():
            controller = LocalConfigController(path)
            folders, files = controller.delete_existing_configs(self.manager)
            message = f'Deleted Files [{len(files)}] / Folders [{len(folders)}] in {controller.full_path}'
            log.info(message)

    def add_icons_to_folders(self, overwrite: bool):
        self.folders_ctrl.icon_configs = self.icons_ctrl.icon_configs
        for folder_path in self.config.search_folder_paths():
            start = len(self.folders_ctrl.icon_folders)
            self.folders_ctrl.add_icon_folders(folder_path, overwrite)
            amount = len(self.folders_ctrl.icon_folders) - start
            log.info(f'Added "{amount}" icons in {folder_path}')

    def create_icon_config_templates(self, overwrite: bool, update: bool) -> None:
        if update:
            self.icons_ctrl.update_icon_config_files()
        else:
            self.icons_ctrl.create_icon_config_files(overwrite)

    def export_app_config_template(self, export_path: str) -> None:
        controller = AppConfigController(export_path)
        controller.export_app_config()
