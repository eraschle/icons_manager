import logging
from typing import Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFile
from icon_manager.crawler.filters import files_by_extension
from icon_manager.helpers.decorator import execution, execution_action
from icon_manager.interfaces.path import File, Folder
from icon_manager.interfaces.actions import Action, DeleteAction
from icon_manager.interfaces.builder import FileCrawlerBuilder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class IconFileBuilder(FileCrawlerBuilder[MatchedIconFile]):

    def __init__(self) -> None:
        super().__init__()
        self.icons_names: Iterable[str] = []

    def setup(self, **kwargs) -> None:
        settings = kwargs.get('settings', [])
        library_icons = [setting.icon for setting in settings]
        self.icons_names = [icon.name for icon in library_icons]

    def can_build_file(self, file: File, **kwargs) -> bool:
        return file.name in self.icons_names

    def build_file_model(self, file: File, **kwargs) -> Optional[MatchedIconFile]:
        return MatchedIconFile(file.path)


class IconFileController(ContentController[MatchedIconFile]):

    def __init__(self, user_config: UserConfig,
                 builder: FileCrawlerBuilder = IconFileBuilder()) -> None:
        super().__init__(user_config, builder)
        self.files: List[MatchedIconFile] = []

    @execution(message='Crawle & build icons (__icon__ folder)')
    def crawle_and_build_result(self, folders: List[Folder], settings: Sequence[IconSetting]):
        extensions = [MatchedIconFile.extension(with_point=False)]
        files = files_by_extension(folders, extensions)
        self.builder.setup(settings=settings)
        self.files = self.builder.build_models(files)

    @execution_action(message='Crawle & build icons (__icon__ folder)')
    def delete_content(self) -> Action:
        action = DeleteAction(self. user_config, self.files)
        action.execute()
        if not action.any_executed():
            return action
        return action
