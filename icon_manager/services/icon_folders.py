from typing import Iterable, List, Optional

from icon_manager.commands.config_command import (ConfigCommand,
                                                  DesktopAttributeCommand,
                                                  IconCommand)
from icon_manager.config.config import ConfigManager
from icon_manager.data.ini_writer import DesktopFileWriter
from icon_manager.models.config import IconConfig
from icon_manager.models.container import ConfiguredContainer, FolderContainer, SearchOption
from icon_manager.models.path import FolderModel, JsonFile, PathModel
from icon_manager.services.factories import ConfigFactory

WRITE_CONFIG_COMMANDS: Iterable[ConfigCommand] = [
    IconCommand(),
    DesktopAttributeCommand()
]


class WriteConfigManager:
    def __init__(self, writer: DesktopFileWriter = DesktopFileWriter(),
                 commands: Iterable[ConfigCommand] = WRITE_CONFIG_COMMANDS) -> None:
        self.writer = writer
        self.commands = commands

    def execute_commands(self, container: ConfiguredContainer, func_name: str) -> ConfiguredContainer:
        for command in self.commands:
            function = getattr(command, func_name)
            function(container)
        return container

    def write_config(self, container: ConfiguredContainer) -> ConfiguredContainer:
        container = self.execute_commands(container, 'pre_command')
        container = self.writer.write_config(container)
        return self.execute_commands(container, 'post_command')


class IconFolderService:
    def __init__(self, config: ConfigManager) -> None:
        self.config = config
        self.folder_configs: List[IconConfig] = []
        self.icon_folders: List[ConfiguredContainer] = []

    def can_add_icons_to_folders(self) -> bool:
        return (len(self.config.folder_configs()) > 0
                and len(self.config.folder_containers()) > 0)

    def read_config(self):
        configs = []
        factory = ConfigFactory(self.config)
        for name, folder_config in self.config.folder_configs().items():
            icon_config = factory.create(folder_config, name=name)
            configs.append(icon_config)
        self.folder_configs = sorted(configs, key=lambda cnf: cnf.order_key())

    def remove_existing_models_in(self, container: FolderContainer) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for model in container.get_existing():
            model.remove()
            removed.append(model)
        return removed

    def remove_existing_models(self):
        removed: List[PathModel] = []
        for container in self.config.folder_containers():
            start_count = len(removed)
            removed.extend(self.remove_existing_models_in(container))
            end_count = len(removed)
            amount = end_count - start_count
            print(f'Removed "{amount}" in {container.path}')
        return removed

    def get_config_for(self, folder: FolderModel, is_root: bool) -> Optional[IconConfig]:
        for config in self.folder_configs:
            if not config.is_config_for(folder, is_root):
                continue
            return config
        return None

    def collect_folder_to_add_icon(self, folder: FolderModel, is_root: bool):
        config = self.get_config_for(folder, is_root)
        if config is None:
            return
        copy_icon = self.config.copy_icon_to_container()
        icon_folder = ConfiguredContainer(folder, config, copy_icon)
        self.icon_folders.append(icon_folder)

    def collect_folder_to_add_icons(self):
        for container in self.config.folder_containers():
            start_count = len(self.icon_folders)
            self.collect_folder_to_add_icon(container, is_root=True)
            for folder_path in container.get_content():
                self.collect_folder_to_add_icon(folder_path, is_root=False)
            end_count = len(self.icon_folders)
            amount = end_count - start_count
            print(f'Collected "{amount}" in {container.path}')

    def add_icons_to_folders(self, manager: WriteConfigManager) -> Iterable[ConfiguredContainer]:
        errors = []
        for icon_folder in self.icon_folders:
            icon_folder = manager.write_config(icon_folder)
            print(f'Add icon to {icon_folder.path}')
            if not icon_folder.has_errors():
                continue
            errors.append(icon_folder)
        return errors

    def copy_template_config(self, container: FolderContainer, template: JsonFile) -> None:
        export_config = container.create_file(template.name, JsonFile)
        template.copy_to(export_config)

    def export_template_config(self, export_path: str) -> None:
        container = FolderContainer(export_path, SearchOption())
        self.copy_template_config(container, self.config.icon_config_file)
        self.copy_template_config(container, self.config.folder_config_file)
