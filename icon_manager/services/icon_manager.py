from typing import Iterable, List

from icon_manager.config.config import AppConfig
from icon_manager.config.creator import ConfigCreator
from icon_manager.controller.config import LocalConfigController
from icon_manager.controller.icons import IconsController
from icon_manager.models.container import ConfiguredContainer
from icon_manager.models.path import FolderModel


class IconFolderService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.icon_controller = IconsController(config)
        self.icon_folders: List[ConfiguredContainer] = []

    def read_config(self):
        self.icon_controller.create_icon_config()

    def remove_existing_configs(self):
        for path in self.config.folders.get_folder_paths():
            controller = LocalConfigController(path)
            removed = controller.delete_existing_configs()
            print(f'Removed "{len(removed)}" in {controller.full_path}')

    def collect_folder_to_add_icon(self, folder: FolderModel):
        config = self.icon_controller.icon_config_for(folder)
        if config is None:
            return
        copy_icon = self.config.copy_icon_to_folder()
        icon_folder = ConfiguredContainer(folder, config, copy_icon)
        self.icon_folders.append(icon_folder)

    def collect_folder_to_add_icons(self):
        for container in self.config.folder_containers():
            start_count = len(self.icon_folders)
            self.collect_folder_to_add_icon(container)
            for folder_path in container.get_content():
                self.collect_folder_to_add_icon(folder_path)
            end_count = len(self.icon_folders)
            amount = end_count - start_count
            print(f'Collected "{amount}" in {container.path}')

    def add_icons_to_folders(self, creator: ConfigCreator) -> Iterable[ConfiguredContainer]:
        errors = []
        for icon_folder in self.icon_folders:
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
