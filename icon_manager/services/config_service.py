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
from icon_manager.interfaces.path import Folder
from icon_manager.library.controller import IconLibraryController
from icon_manager.rules.manager import ExcludeManager

log = logging.getLogger(__name__)


class ConfigService:
    """Everything the icon manager does for a single user configuration.

    Orchestrates the icon library (which icon belongs to which rule set),
    the crawler (which folders exist) and the content controllers (which
    desktop.ini files, __icon__ folders and icon files are on disk).
    """

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
    def create_settings(self):
        """Read the icon library from disk and pair icons with their rules."""
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
        """Merge the application-wide before/after affixes into this config's."""
        self._before_or_after.update(before_and_after)
        self._before_or_after.update(self.user_config.before_or_after)

    def set_exclude_manager(self, exclude: ExcludeManager):
        """Install the exclude rules, prepared with the affixes collected so far.

        Must run after :meth:`update_before_and_after`, otherwise the exclude
        rules match only the literal values from the config file.
        """
        exclude.setup_rules(self._before_or_after)
        exclude.clean_empty()
        self.__exclude = exclude

    @execution(message="Found & applied icons", start_message="Start find & apply icons")
    def find_and_apply_matches(self):
        """Crawl the search folders, match them against the icon settings and
        write a desktop.ini for every match."""
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
        return async_crawling_folders(self.user_config.name, folders)

    @execution(message="Crawled through content")
    def find_existing_content(self):
        """Catalog what this tool previously wrote: desktop.ini files,
        __icon__ folders and the icon files copied into them."""
        entries = self.crawling_search_folders()
        settings = self.settings.settings(clean_empty=True)
        self.desktop.crawle_and_build_result(entries, settings)
        self.icon_folders.crawle_and_build_result(entries, settings)
        self.icon_files.crawle_and_build_result(entries, settings)

    @execution(message="RE-Applied icons")
    def re_apply_icons(self):
        """Re-write desktop.ini for folders that still have a copied icon.

        OneDrive synchronisation drops the desktop.ini but keeps the
        __icon__ folder, so the icon can be restored without crawling rules.
        """
        controller = ReApplyController(self.settings, self.icon_folders)
        self.rules.re_apply_matches(controller)

    @execution(message="Deleted content", start_message="Start delete content")
    def delete_content(self):
        """Remove everything this tool wrote, found by :meth:`find_existing_content`."""
        self.desktop.delete_content()
        self.icon_folders.delete_content()
        self.icon_files.delete_content()
