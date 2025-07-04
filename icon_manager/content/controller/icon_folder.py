import logging
from collections.abc import Iterable, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFolder
from icon_manager.crawler.filters import folders_by_name
from icon_manager.helpers.decorator import execution
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import FolderCrawlerBuilder
from icon_manager.interfaces.path import Folder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class IconFolderBuilder(FolderCrawlerBuilder[MatchedIconFolder]):
    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return folder.name == MatchedIconFolder.folder_name

    def build_folder_model(self, folder: Folder, **kwargs) -> MatchedIconFolder | None:
        return MatchedIconFolder(folder.path)


class IconFolderController(ContentController[MatchedIconFolder]):
    def __init__(
        self,
        user_config: UserConfig,
        builder: FolderCrawlerBuilder = IconFolderBuilder(),
    ) -> None:
        super().__init__(user_config, builder)
        self.folders: list[MatchedIconFolder] = []

    @execution(message="Crawle & build __icon__ folder")
    def crawle_and_build_result(self, folders: list[Folder], _: Sequence[IconSetting]):
        folders = folders_by_name(folders, [MatchedIconFolder.folder_name])
        self.folders = self.builder.build_models(folders)

    @execution(message="Deleted existing __icon__ folder")
    def delete_content(self) -> None:
        action = DeleteAction(self.folders)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedIconFolder))

    def folders_with_icon(self) -> Iterable[MatchedIconFolder]:
        return [folder for folder in self.folders if len(folder.get_icons()) > 0]
