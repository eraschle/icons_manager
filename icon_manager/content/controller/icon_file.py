import logging
from collections.abc import Callable, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFile
from icon_manager.crawler.filters import files_by_extension
from icon_manager.helpers.decorator import execution, execution_action
from icon_manager.interfaces.actions import Action, DeleteAction
from icon_manager.interfaces.builder import FileCrawlerBuilder
from icon_manager.interfaces.path import File, Folder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class IconFileBuilder(FileCrawlerBuilder[MatchedIconFile]):
    """Finds the icon files this tool copied into __icon__ folders."""

    def __init__(self, settings: Sequence[IconSetting]) -> None:
        self.icon_names = {setting.icon.name for setting in settings}

    def can_build_file(self, file: File) -> bool:
        return file.name in self.icon_names

    def build_file_model(self, file: File) -> MatchedIconFile | None:
        return MatchedIconFile(file.path)


class IconFileController(ContentController[MatchedIconFile]):
    def __init__(
        self,
        user_config: UserConfig,
        make_builder: Callable[[Sequence[IconSetting]], FileCrawlerBuilder[MatchedIconFile]] = IconFileBuilder,
    ) -> None:
        self.user_config = user_config
        self.make_builder = make_builder
        self.files: list[MatchedIconFile] = []

    @execution(message="Crawle & build icons (__icon__ folder)")
    def crawle_and_build_result(self, folders: list[Folder], settings: Sequence[IconSetting]) -> None:
        extensions = [MatchedIconFile.extension(with_point=False)]
        files = files_by_extension(folders, extensions)
        self.files = self.make_builder(settings).build_models(files)

    @execution_action(message="Crawle & build icons (__icon__ folder)")
    def delete_content(self) -> Action:
        action = DeleteAction(self.user_config.name, self.files)
        action.execute()
        return action
