from typing import Iterable, Optional, Protocol

from icon_manager.source.ini_source import DesktopFileSource
from icon_manager.handler.icon_config import IconFolderHandler
from icon_manager.models.path import DesktopIniFile


class ConfigCommand(Protocol):

    def pre_command(self, container: IconFolderHandler):
        pass

    def post_command(self, container: IconFolderHandler):
        pass


class IconCommand(ConfigCommand):

    def pre_command(self, container: IconFolderHandler):
        if not container.config.copy_icon:
            return
        try:
            copied_icon = container.copy_icon_to_local_folder()
            container.config.icon_file = copied_icon
        except Exception as ex:
            container.add_error('copy icon to local', ex)

    def post_command(self, container: IconFolderHandler):
        if not container.config.copy_icon:
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

    def pre_command(self, container: IconFolderHandler):
        if not container.ini_file.exists():
            return
        try:
            container.ini_file.set_writeable_and_visible()
        except Exception as ex:
            container.add_error('before apply config', ex)

    def post_command(self, container: IconFolderHandler):
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


class DesktopIniHandler:

    app_entry = 'IconManager=1'

    def __init__(self, source: DesktopFileSource = DesktopFileSource(),
                 commands: Iterable[ConfigCommand] = WRITE_CONFIG_COMMANDS) -> None:
        self.source = source
        self.commands = commands

    def get_ini_lines(self, handler: IconFolderHandler) -> Iterable[str]:
        icon_path = handler.config_icon_path()
        return [
            '[.ShellClassInfo]',
            f'IconResource={icon_path},0',
            DesktopIniHandler.app_entry,
            '[ViewState]',
            'Mode=',
            'Vid=',
            'FolderType=Generic'
        ]

    def execute_commands(self, handler: IconFolderHandler, func_name: str) -> None:
        for command in self.commands:
            function = getattr(command, func_name)
            function(handler)

    def write_config(self, handler: IconFolderHandler) -> IconFolderHandler:
        self.execute_commands(handler, 'pre_command')
        try:
            self.source.write(handler.ini_file,
                              self.get_ini_lines(handler))
        except Exception as ex:
            handler.add_error('Write file', ex)
        self.execute_commands(handler, 'post_command')
        return handler

    def get_app_entry(self, file: DesktopIniFile) -> Optional[str]:
        content_lines = self.source.read(file)
        for line in content_lines:
            if DesktopIniHandler.app_entry not in line:
                continue
            return line
        return None

    def is_app_desktop_file(self, file: DesktopIniFile) -> bool:
        if not file.exists():
            return False
        app_entry = self.get_app_entry(file)
        return app_entry is not None
