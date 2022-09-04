import logging
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Sequence, Union

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.desktop import DesktopIniFile
from icon_manager.content.models.matched import (MatchedIconFile,
                                                 MatchedIconFolder,
                                                 MatchedRuleFolder)
from icon_manager.crawler.filters import files_by_extension
from icon_manager.crawler.options import FilterOptions
from icon_manager.data.ini_source import DesktopFileSource
from icon_manager.helpers.path import File, Folder
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.library.models import IconSetting, LibraryIconFile
from icon_manager.interfaces.path import PathModel

log = logging.getLogger(__name__)


# region MATCHED DESKTOP INI


class DesktopIniBuilder(CrawlerBuilder[DesktopIniFile]):

    app_entry = 'IconManager=1'
    source: DesktopFileSource = DesktopFileSource()

    @classmethod
    def is_file_from_app(cls, file: Union[File, PathModel]) -> bool:
        if isinstance(file, DesktopIniFile):
            source_file = file
        else:
            source_file = DesktopIniFile(file.path)
        content_lines = cls.source.read(source_file)
        for line in content_lines:
            if cls.app_entry not in line:
                continue
            return True
        return False

    def can_build_file(self, file: File, **kwargs) -> bool:
        return (DesktopIniFile.is_model(file.path)
                and self.is_file_from_app(file))

    def build_file_model(self, file: File, **kwargs) -> Optional[DesktopIniFile]:
        return DesktopIniFile(file.path)


class DesktopIniOptions(FilterOptions):
    def __init__(self) -> None:
        super().__init__(clean_excluded=True, clean_project=True, clean_recursive=True)


class DesktopIniController(ContentController[DesktopIniFile]):

    def __init__(self, user_config: UserConfig,
                 builder: CrawlerBuilder = DesktopIniBuilder(),
                 options: FilterOptions = DesktopIniOptions()) -> None:
        super().__init__(user_config, builder, options)
        self.desktop_files: List[DesktopIniFile] = []

    def crawl_content(self, folders: List[Folder], _: Sequence[IconSetting]):
        extensions = [DesktopIniFile.extension(with_point=False)]
        files = files_by_extension(folders, extensions)
        self.desktop_files = self.builder.build_models(files)

    def delete_content(self):
        action = DeleteAction(self.desktop_files)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(DesktopIniFile))


# endregion


# region COMMANDS


class ConfigCommand(ABC):

    def __init__(self, order: int, copy_icon: bool) -> None:
        super().__init__()
        self.order = order
        self.copy_icon = copy_icon

    @abstractmethod
    def pre_command(self):
        pass

    @abstractmethod
    def post_command(self):
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__


def error_message(model: PathModel, message: str) -> str:
    return f'{model.name} >> "{message}"'


class RuleFolderCommand(ConfigCommand):

    def __init__(self, order: int, copy_icon: bool, rule_folder: MatchedRuleFolder) -> None:
        super().__init__(order, copy_icon)
        self.rule_folder = rule_folder

    def pre_command(self):
        if not self.copy_icon or self.rule_folder.icon_folder.exists():
            return
        try:
            self.rule_folder.icon_folder.create()
        except Exception as ex:
            message = 'icon folder create [pre command]'
            log.exception(error_message(self.rule_folder, message), ex)

    def post_command(self):
        if not self.rule_folder.exists():
            return
        try:
            self.rule_folder.set_read_only(is_read_only=True)
        except Exception as ex:
            message = 'set attribute [post command]'
            log.exception(error_message(self.rule_folder, message), ex)


class IconFolderCommand(ConfigCommand):

    def __init__(self, order: int, copy_icon: bool, icon_folder: MatchedIconFolder) -> None:
        super().__init__(order, copy_icon)
        self.icon_folder = icon_folder

    def pre_command(self):
        if not self.copy_icon or self.icon_folder.exists():
            return
        try:
            self.icon_folder.create()
        except Exception as ex:
            message = 'create folder [pre command]'
            log.exception(error_message(self.icon_folder, message), ex)

    def post_command(self):
        if not self.icon_folder.exists():
            return
        try:
            self.icon_folder.set_hidden(is_hidden=True)
        except Exception as ex:
            message = 'set attribute [post command]'
            log.exception(error_message(self.icon_folder, message), ex)


class IconFileCommand(ConfigCommand):

    def __init__(self, order: int, copy_icon: bool, icon: MatchedIconFile,
                 library: LibraryIconFile) -> None:
        super().__init__(order, copy_icon)
        self.icon = icon
        self.library = library

    def pre_command(self):
        if not self.copy_icon or self.icon.exists():
            return
        try:
            self.library.copy_to(self.icon)
        except Exception as ex:
            log.exception(error_message(self.icon, 'copy library icon'), ex)

    def post_command(self):
        if not self.icon.exists():
            return
        try:
            self.icon.set_hidden(is_hidden=True)
        except Exception as ex:
            log.exception(error_message(self.icon, 'icon file attribute'), ex)


class DesktopAttributeCommand(ConfigCommand):

    def __init__(self, order: int, copy_icon: bool, desktop: DesktopIniFile) -> None:
        super().__init__(order, copy_icon)
        self.desktop = desktop

    def pre_command(self):
        if not self.desktop.exists():
            return
        try:
            self.desktop.set_writeable_and_visible()
        except Exception as ex:
            message = 'set attribute [pre command]'
            log.exception(error_message(self.desktop, message), ex)

    def post_command(self):
        if not self.desktop.exists():
            return
        try:
            self.desktop.set_protected_and_hidden()
        except Exception as ex:
            message = 'set attribute [post command]'
            log.exception(error_message(self.desktop, message), ex)


# endregion


# region DESKTOP INI CONTROLLER


def get_commands(rule_folder: MatchedRuleFolder, copy_icon: bool) -> List[ConfigCommand]:
    icon_folder = rule_folder.icon_folder
    local_icon = rule_folder.local_icon
    library_icon = rule_folder.library_icon
    return [
        RuleFolderCommand(1, copy_icon, rule_folder),
        IconFolderCommand(2, copy_icon, icon_folder),
        IconFileCommand(3, copy_icon, local_icon, library_icon),
        DesktopAttributeCommand(4, copy_icon, rule_folder.desktop_ini)
    ]


class DesktopIniCreator:

    def __init__(self, source: DesktopFileSource = DesktopFileSource()) -> None:
        self.source = source
        self.commands: List[ConfigCommand] = []

    def can_write(self, file: DesktopIniFile) -> bool:
        if not file.exists():
            return True
        return DesktopIniBuilder.is_file_from_app(file)

    def create_content(self, manager: MatchedRuleFolder) -> Iterable[str]:
        return [
            '[.ShellClassInfo]',
            f'IconResource={manager.icon_path_for_desktop_ini()},0',
            DesktopIniBuilder.app_entry,
            '[ViewState]',
            'Mode=',
            'Vid=',
            'FolderType=Generic'
        ]

    def order_commands(self, reverse: bool) -> None:
        self.commands.sort(key=lambda cmd: cmd.order, reverse=reverse)

    def execute_commands(self, func_name: str) -> None:
        for command in self.commands:
            function = getattr(command, func_name)
            function()

    def write(self, folder: MatchedRuleFolder, copy_icon: bool) -> None:
        self.commands = get_commands(folder, copy_icon)
        self.order_commands(reverse=False)
        self.execute_commands('pre_command')
        try:
            self.source.write(folder.desktop_ini,
                              self.create_content(folder))
        except Exception as ex:
            log.exception(error_message(folder, 'Write desktop.ini'), ex)
        self.order_commands(reverse=True)
        self.execute_commands('post_command')


# endregion
