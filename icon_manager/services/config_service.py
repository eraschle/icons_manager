import logging
from collections.abc import Iterable

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.crawler.crawler import async_crawling_folders, crawling_icons
from icon_manager.helpers.decorator import execution
from icon_manager.interfaces.path import File, Folder
from icon_manager.library.controller import IconLibraryController
from icon_manager.rules.manager import ExcludeManager
from icon_manager.services.base import IConfigService

log = logging.getLogger(__name__)


class ConfigService(IConfigService):
    def __init__(
        self,
        user_config: UserConfig,
        settings: IconLibraryController,
        desktop: DesktopIniController,
        icon_folders: IconFolderController,
        icon_files: IconFileController,
        rules: RulesApplyController,
    ) -> None:
        self.user_config = user_config
        self.settings = settings
        self.desktop = desktop
        self.icon_folders = icon_folders
        self.icon_files = icon_files
        self.rules = rules
        self.__exclude: ExcludeManager | None = None
        self._before_or_after: set[str] = set()

    @property
    def exclude(self) -> ExcludeManager:
        if self.__exclude is None:
            message = f"{type(ExcludeManager)} has not been set or is None"
            raise ValueError(message)
        return self.__exclude

    @execution(message="Created icon settings")
    def create_settings(self, content: dict[str, list[File]]):
        extensions = IconLibraryController.icons_extensions
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

    def update_before_and_after(self, before_and_after: Iterable[str]):
        self._before_or_after.update(before_and_after)
        self._before_or_after.update(self.user_config.before_or_after)

    def set_exclude_manager(self, exclude: ExcludeManager):
        exclude.setup_rules(self._before_or_after)
        exclude.clean_empty()
        self.__exclude = exclude

    @execution(
        message="Found & applied icons",
        start_message="Start find & apply icons",
    )
    def find_and_apply_matches(self):
        settings = self.settings.create_icon_settings(self._before_or_after)
        entries = self.crawling_search_folders()
        entries = self.rules.crawle_and_build_result(entries, self.exclude)
        self.rules.search_and_find_matches(entries, settings)
        self.rules.creating_found_matches(self.exclude)

    @execution(
        message="Crawled through folders (No filtering)",
        start_message="Crawling search folders",
    )
    def crawling_search_folders(self) -> list[Folder]:
        folders = self.user_config.search_folders
        return async_crawling_folders(folders)

    @execution(message="Crawled through content")
    def find_existing_content(self):
        entries = self.crawling_search_folders()
        settings = self.settings.settings(clean_empty=True)
        self.desktop.crawle_and_build_result(entries, settings)
        self.icon_folders.crawle_and_build_result(entries, settings)
        self.icon_files.crawle_and_build_result(entries, settings)

    @execution(message="RE-Applied icons")
    def re_apply_icons(self):
        controller = ReApplyController(self.settings, self.icon_folders)
        self.rules.re_apply_matches(controller)

    @execution(message="Deleted content", start_message="Start delete content")
    def delete_content(self):
        self.desktop.delete_content()
        self.icon_folders.delete_content()
        self.icon_files.delete_content()
