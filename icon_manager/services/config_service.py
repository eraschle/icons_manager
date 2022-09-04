import logging

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.controller.rules_apply import IApplyController
from icon_manager.crawler.crawler import (crawling_icons,
                                          crawling_search_folders)
from icon_manager.library.controller import (IconSettingController,
                                             SettingsControllerInterface)
from icon_manager.services.base import IConfigService

log = logging.getLogger(__name__)


class ConfigService(IConfigService):

    def __init__(self, user_config: UserConfig, settings: SettingsControllerInterface,
                 desktop: DesktopIniController, icon_folders: IconFolderController,
                 icon_files: IconFileController, rules: IApplyController) -> None:
        self.user_config = user_config
        self.settings = settings
        self.desktop = desktop
        self.icon_folders = icon_folders
        self.icon_files = icon_files
        self.rules = rules

    def create_settings(self):
        extensions = IconSettingController.icons_extensions
        content = crawling_icons(self.user_config.icons_path, extensions)
        self.settings.create_settings(content)

    def create_icon_configs(self, overwrite: bool):
        self.settings.create_icon_configs(overwrite)

    def update_icon_configs(self):
        self.settings.update_icon_configs()

    def delete_icon_configs(self):
        self.settings.delete_icon_configs()

    def archive_library(self):
        self.settings.archive_library()

    def crawl_content(self, find_matches: bool):
        self._crawle_search_folders()
        if find_matches:
            self._find_matching_content()

    def _crawle_search_folders(self):
        entries = crawling_search_folders(self.user_config.search_folders)
        settings = self.settings.settings(clean_empty=False)
        self.desktop.crawl_content(entries, settings)
        self.icon_folders.crawl_content(entries, settings)
        self.icon_files.crawl_content(entries, settings)
        self.rules.crawl_content(entries)

    def _find_matching_content(self):
        settings = self.settings.settings(clean_empty=True)
        self.rules.find_matches(settings)

    def apply_icons(self):
        self.rules.apply_matches()

    def re_apply_icons(self):
        controller = ReApplyController(self.settings, self.desktop,
                                       self.icon_folders)
        self.rules.re_apply_matches(controller)

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
