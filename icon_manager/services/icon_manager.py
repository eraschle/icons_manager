from typing import Iterable

from icon_manager.config.config import AppConfig
from icon_manager.config.creator import ConfigCreator
from icon_manager.controller.config import LocalConfigController
from icon_manager.controller.folder import IconFolderController
from icon_manager.controller.icons import IconsController
from icon_manager.models.container import IconContainer


class IconFolderService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.icons_ctrl = IconsController(config)
        self.folders_ctrl = IconFolderController()

    def read_config(self):
        self.icons_ctrl.create_icon_config()

    def remove_existing_configs(self):
        for path in self.config.folders.get_search_folder_paths():
            controller = LocalConfigController(path)
            removed = controller.delete_existing_configs()
            print(f'Removed "{len(removed)}" in {controller.full_path}')

    def collect_folder_to_add_icons(self, overwrite: bool):
        self.folders_ctrl.icon_configs = self.icons_ctrl.icon_configs
        for folder_path in self.config.search_folder_paths():
            self.folders_ctrl.collect_icon_folders(folder_path,
                                                   overwrite)
            # print(f'Collected "{amount}" in {folder_path.path}')

    def add_icons_to_folders(self, creator: ConfigCreator) -> Iterable[IconContainer]:
        errors = []
        for icon_folder in self.folders_ctrl.icon_folders:
            icon_folder = creator.write_config(icon_folder)
            print(f'Add icon to {icon_folder.path}')
            if not icon_folder.has_errors():
                continue
            errors.append(icon_folder)
        return errors

    def export_config_templates(self, overwrite: bool, update: bool) -> None:
        if update:
            self.icons_ctrl.update_icon_config_files()
        else:
            self.icons_ctrl.create_icon_config_files(overwrite)
