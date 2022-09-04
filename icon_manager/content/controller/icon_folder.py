import logging
from typing import Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFolder
from icon_manager.crawler.filters import folders_by_name
from icon_manager.crawler.options import FilterOptions
from icon_manager.helpers.path import Folder
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class IconFolderBuilder(CrawlerBuilder[MatchedIconFolder]):

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return folder.name == MatchedIconFolder.folder_name

    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[MatchedIconFolder]:
        return MatchedIconFolder(folder.path)


class IconFolderOptions(FilterOptions):
    def __init__(self) -> None:
        super().__init__(clean_excluded=False, clean_project=False, clean_recursive=False)


class IconFolderController(ContentController[MatchedIconFolder]):

    def __init__(self, user_config: UserConfig,
                 builder: CrawlerBuilder = IconFolderBuilder(),
                 options: FilterOptions = IconFolderOptions()) -> None:
        super().__init__(user_config, builder, options)
        self.folders: List[MatchedIconFolder] = []

    def crawl_content(self, folders: List[Folder], _: Sequence[IconSetting]):
        folders = folders_by_name(folders, [MatchedIconFolder.folder_name])
        self.folders = self.builder.build_models(folders)

    def delete_content(self) -> None:
        action = DeleteAction(self.folders)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedIconFolder))

    def folders_with_icon(self) -> Iterable[MatchedIconFolder]:
        return [folder for folder in self.folders if len(folder.get_icons()) > 0]
