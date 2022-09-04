import logging
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFile
from icon_manager.crawler.filters import files_by_extension
from icon_manager.crawler.options import FilterOptions
from icon_manager.helpers.logs import log_time
from icon_manager.helpers.path import File, Folder
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.library.models import IconSetting, LibraryIconFile

log = logging.getLogger(__name__)


class IconFileBuilder(CrawlerBuilder[MatchedIconFile]):

    def __init__(self) -> None:
        super().__init__()
        self.icons_names: Iterable[LibraryIconFile] = []

    def setup(self, **kwargs) -> None:
        settings = kwargs.get('settings', [])
        library_icons = [setting.icon for setting in settings]
        self.icons_names = [icon.name for icon in library_icons]

    def can_build_file(self, file: File, **kwargs) -> bool:
        return file.name in self.icons_names

    def build_file_model(self, file: File, **kwargs) -> Optional[MatchedIconFile]:
        return MatchedIconFile(file.path)


class IconFileOptions(FilterOptions):
    def __init__(self) -> None:
        super().__init__(clean_excluded=False, clean_project=False, clean_recursive=False)


class IconFileController(ContentController[MatchedIconFile]):

    def __init__(self, user_config: UserConfig,
                 builder: CrawlerBuilder = IconFileBuilder(),
                 options: FilterOptions = IconFileOptions()) -> None:
        super().__init__(user_config, builder, options)
        self.files: List[MatchedIconFile] = []

    def crawl_content(self, folders: List[Folder], settings: Sequence[IconSetting]):
        start = datetime.now()
        extensions = [MatchedIconFile.extension(with_point=False)]
        files = files_by_extension(folders, extensions)
        self.builder.setup(settings=settings)
        self.files = self.builder.build_models(files)
        log.info(log_time('Build copied icons', start))

    def delete_content(self) -> None:
        action = DeleteAction(self.files)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedIconFile))
