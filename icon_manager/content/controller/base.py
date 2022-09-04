import logging
from abc import ABC, abstractmethod
from typing import Generic, List, Sequence, TypeVar

from icon_manager.config.user import UserConfig
from icon_manager.crawler.options import FilterOptions
from icon_manager.helpers.path import Folder
from icon_manager.interfaces.controller import IContentController
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


TModel = TypeVar('TModel', bound=object)


class ContentController(ABC, IContentController, Generic[TModel]):

    def __init__(self, user_config: UserConfig, builder: CrawlerBuilder[TModel],
                 options: FilterOptions) -> None:
        self.user_config = user_config
        self.builder = builder
        self.options = options

    @abstractmethod
    def crawl_content(self, folders: List[Folder], settings: Sequence[IconSetting]):
        pass

    @abstractmethod
    def delete_content(self):
        pass
