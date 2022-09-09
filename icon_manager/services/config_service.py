import logging
from typing import Iterable, List, Optional, Set

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.crawler.crawler import async_crawling_folders, crawling_icons
from icon_manager.helpers.decorator import execution
from icon_manager.helpers.path import Folder
from icon_manager.library.controller import (IconSettingController,
                                             ISettingsController)
from icon_manager.rules.manager import ExcludeManager
from icon_manager.services.base import IConfigService

log = logging.getLogger(__name__)


class ConfigService(IConfigService):

    def __init__(self, user_config: UserConfig, settings: ISettingsController,
                 desktop: DesktopIniController, icon_folders: IconFolderController,
                 icon_files: IconFileController, rules: RulesApplyController) -> None:
        self.user_config = user_config
        self.settings = settings
        self.desktop = desktop
        self.icon_folders = icon_folders
        self.icon_files = icon_files
        self.rules = rules
        self.__exclude: Optional[ExcludeManager] = None
        self._before_or_after: Set[str] = set()

    @property
    def exclude(self) -> ExcludeManager:
        if self.__exclude is None:
            message = f'{type(ExcludeManager)} has not been set or is None'
            raise ValueError(message)
        return self.__exclude

    @execution(message='Created icon settings')
    def create_settings(self):
        extensions = IconSettingController.icons_extensions
        content = crawling_icons(self.user_config.icons_path, extensions)
        self.settings.create_settings(content)

    def create_icon_configs(self):
        self.settings.create_icon_configs()

    def update_icon_configs(self):
        self.settings.update_icon_configs()

    def delete_icon_configs(self):
        self.settings.delete_icon_configs()

    def archive_library(self):
        self.settings.archive_library()

    def update_before_and_after(self, before_or_after: Iterable[str]):
        self._before_or_after.update(before_or_after)
        self._before_or_after.update(self.user_config.before_or_after)

    def set_exclude_manager(self, exclude: ExcludeManager):
        exclude.setup_rules(self._before_or_after)
        exclude.clean_empty()
        self.__exclude = exclude

    @execution(message='Found & applied icons', start_message='Start find & apply icons')
    def find_and_apply_matches(self):
        settings = self.settings.create_icon_settings(self._before_or_after)
        entries = self.crawling_search_folders()
        entries = self.rules.crawle_and_build_result(entries, self.exclude)
        self.rules.search_and_find_matches(entries, settings)
        self.rules.creating_found_matches(self.exclude)

    @execution(message='Crawled through folders (No filtering)', start_message='Crawling search folders')
    def crawling_search_folders(self) -> List[Folder]:
        folders = self.user_config.search_folders
        return async_crawling_folders(folders)

    @execution(message='Crawled through content')
    def find_existing_content(self):
        entries = self.crawling_search_folders()
        settings = self.settings.settings(clean_empty=True)
        self.desktop.crawle_and_build_result(entries, settings)
        self.icon_folders.crawle_and_build_result(entries, settings)
        self.icon_files.crawle_and_build_result(entries, settings)

    @ execution(message='RE-Applied icons')
    def re_apply_icons(self):
        controller = ReApplyController(self.settings, self.desktop,
                                       self.icon_folders)
        self.rules.re_apply_matches(controller)

    @ execution(message='Deleted content', start_message='Start delete content')
    def delete_content(self):
        self.desktop.delete_content()
        self.icon_folders.delete_content()
        self.icon_files.delete_content()

    # def get_icon_config_by(self, local_folder: MatchedIconFolder) -> Optional[IconSetting]:
    #     icon_file = self.icon_file_by(local_folder)
    #     if icon_file is None:
    #         return None
    #     return self.icon_config_by(icon_file)

    # def get_icon_folder(self, local_folder: MatchedIconFolder) -> Optional[MatchedRuleFolder]:
    #     icon_config = self.get_icon_config_by(local_folder)
    #     if icon_config is None:
    #         return None
    #     folder = local_folder.parent_folder()
    #     return MatchedRuleFolder(folder, icon_config, self.user_config.copy_icon)

    # def can_write(self, folder: MatchedRuleFolder) -> bool:
    #     if not folder.desktop_ini.exists():
    #         return True
    #     if folder.desktop_ini.exists() and not self.overwrite:
    #         return False
    #     can_write = DesktopFileManager.can_write(folder.desktop_ini)
    #     if not can_write:
    #         log.warning(f'Can not write desktop.ini in "{folder.path}"')
    #     return can_write and self.overwrite
