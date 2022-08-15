import logging
from typing import Iterable, Protocol

from icon_manager.data.ini_source import DesktopFileSource
from icon_manager.managers.icon_folder import IconFolderManager
from icon_manager.models.path import DesktopIniFile

log = logging.getLogger(__name__)


class ConfigCommand(Protocol):

    def pre_command(self, manager: IconFolderManager):
        pass

    def post_command(self, manager: IconFolderManager):
        pass


def error_message(manager: IconFolderManager, message: str) -> str:
    return f'{manager.name} >> "{message}"'


class IconCommand(ConfigCommand):

    def pre_command(self, manager: IconFolderManager):
        if not manager.config.copy_icon:
            return
        try:
            copied_icon = manager.copy_icon_to_local_folder()
            manager.config.icon_file = copied_icon
        except Exception as ex:
            log.exception(error_message(manager, 'copy icon to local'), ex)

    def post_command(self, manager: IconFolderManager):
        if not manager.config.copy_icon:
            return
        try:
            local_folder = manager.local_icon_folder()
            local_folder.set_hidden(is_hidden=True)
        except Exception as ex:
            log.exception(error_message(manager, 'folder attribute'), ex)
            # local_folder.set_read_only(is_read_only=True)
        try:
            local_icon = manager.local_icon_file()
            local_icon.set_hidden(is_hidden=True)
        except Exception as ex:
            log.exception(error_message(manager, 'file attribute'), ex)


class DesktopAttributeCommand(ConfigCommand):

    def pre_command(self, manager: IconFolderManager):
        if not manager.ini_file.exists():
            return
        try:
            manager.ini_file.set_writeable_and_visible()
        except Exception as ex:
            log.exception(error_message(manager, 'before apply config'), ex)

    def post_command(self, manager: IconFolderManager):
        if not manager.ini_file.exists():
            return
        try:
            manager.ini_file.set_protected_and_hidden()
            manager.set_read_only(is_read_only=True)
        except Exception as ex:
            log.exception(error_message(manager, 'after apply config'), ex)


WRITE_CONFIG_COMMANDS: Iterable[ConfigCommand] = [
    IconCommand(),
    DesktopAttributeCommand()
]


class DesktopFileManager:

    app_entry = 'IconManager=1'

    def __init__(self, source: DesktopFileSource = DesktopFileSource(),
                 commands: Iterable[ConfigCommand] = WRITE_CONFIG_COMMANDS) -> None:
        self.source = source
        self.commands = commands

    def get_ini_lines(self, manager: IconFolderManager) -> Iterable[str]:
        icon_path = manager.config_icon_path()
        return [
            '[.ShellClassInfo]',
            f'IconResource={icon_path},0',
            DesktopFileManager.app_entry,
            '[ViewState]',
            'Mode=',
            'Vid=',
            'FolderType=Generic'
        ]

    def execute_commands(self, manager: IconFolderManager, func_name: str) -> None:
        for command in self.commands:
            function = getattr(command, func_name)
            function(manager)

    def write_config(self, manager: IconFolderManager) -> None:
        self.execute_commands(manager, 'pre_command')
        try:
            self.source.write(manager.ini_file,
                              self.get_ini_lines(manager))
        except Exception as ex:
            log.exception(error_message(manager, 'Write desktop.ini'), ex)
        self.execute_commands(manager, 'post_command')

    def can_write_config(self, ini_file: DesktopIniFile) -> bool:
        if not ini_file.exists():
            return True
        return self.is_app_config_file(ini_file)

    def can_delete_config(self, ini_file: DesktopIniFile) -> bool:
        if not ini_file.exists():
            return False
        return self.is_app_config_file(ini_file)

    def is_app_config_file(self, file: DesktopIniFile) -> bool:
        content_lines = self.source.read(file)
        for line in content_lines:
            if DesktopFileManager.app_entry not in line:
                continue
            return True
        return False
