from typing import Iterable, Protocol

from icon_manager.data.ini_writer import DesktopFileWriter
from icon_manager.models.container import ConfiguredContainer


class ConfigCommand(Protocol):

    def pre_command(self, container: ConfiguredContainer):
        pass

    def post_command(self, container: ConfiguredContainer):
        pass


class IconCommand(ConfigCommand):

    def pre_command(self, container: ConfiguredContainer):
        if not container.copy_icon:
            return
        try:
            copied_icon = container.copy_icon_to_local_folder()
            container.config.icon_file = copied_icon
        except Exception as ex:
            container.add_error('copy icon to local', ex)

    def post_command(self, container: ConfiguredContainer):
        if not container.copy_icon:
            return
        try:
            local_folder = container.local_icon_folder()
            local_folder.set_hidden(is_hidden=True)
            # local_folder.set_read_only(is_read_only=True)
            local_icon = container.local_icon_file()
            local_icon.set_hidden(is_hidden=True)
        except Exception as ex:
            container.add_error('set attribute local icon container', ex)


class DesktopAttributeCommand(ConfigCommand):

    def pre_command(self, container: ConfiguredContainer):
        if not container.ini_file.exists():
            return
        try:
            container.ini_file.set_writeable_and_visible()
        except Exception as ex:
            container.add_error('before apply config', ex)

    def post_command(self, container: ConfiguredContainer):
        if not container.ini_file.exists():
            return
        try:
            container.ini_file.set_protected_and_hidden()
            container.set_read_only(is_read_only=True)
        except Exception as ex:
            container.add_error('after apply config', ex)


WRITE_CONFIG_COMMANDS: Iterable[ConfigCommand] = [
    IconCommand(),
    DesktopAttributeCommand()
]


class ConfigCreator:
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
