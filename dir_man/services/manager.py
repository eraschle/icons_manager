from typing import Any, Dict, Iterable, List, Optional

from dir_man.commands.config_command import (ConfigCommand,
                                             DesktopAttributeCommand,
                                             IconCommand)
from dir_man.data.ini_writer import DesktopFileWriter
from dir_man.models.config import IconConfig
from dir_man.models.container import ConfiguredContainer, FolderContainer
from dir_man.models.path import FolderModel, PathModel
from dir_man.services.factories import ConfigFactory

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


class FolderManager:
    def __init__(self) -> None:
        self.folder_configs: List[IconConfig] = []
        self.icon_folders: List[ConfiguredContainer] = []
        self.copy_icon = False
        self.stop_if_git = True

    def read_config(self, user_config: Dict[str, Any]):
        configs = []
        config_section = user_config.pop('config')
        self.copy_icon = config_section.pop('copy_icon', False)
        self.stop_if_git = config_section.pop('stop_if_git', True)
        factory = ConfigFactory(config_section)
        for name, folder_config in config_section.items():
            config = factory.create(folder_config, name=name)
            configs.append(config)
        self.folder_configs = sorted(configs, key=lambda cnf: cnf.order_key())

    def remove_existing_models_in(self, container: FolderContainer) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for model in container.get_existing():
            model.remove()
            removed.append(model)
        return removed

    def remove_existing_models(self, containers: Iterable[FolderContainer]):
        removed: List[PathModel] = []
        for container in containers:
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
        icon_folder = ConfiguredContainer(folder, config, self.copy_icon)
        self.icon_folders.append(icon_folder)

    def collect_folder_to_add_icons(self, containers: Iterable[FolderContainer]):
        for container in containers:
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
