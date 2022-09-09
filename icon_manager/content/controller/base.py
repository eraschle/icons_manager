import logging
from abc import ABC, abstractmethod
from typing import Generic, List, Sequence, TypeVar

from icon_manager.config.user import UserConfig
from icon_manager.helpers.path import Folder
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.library.models import IconSetting
from icon_manager.rules.manager import ExcludeManager

log = logging.getLogger(__name__)


TModel = TypeVar('TModel', bound=object)


class ContentController(ABC, Generic[TModel]):

    def __init__(self, user_config: UserConfig, builder: CrawlerBuilder[TModel]) -> None:
        self.user_config = user_config
        self.builder = builder

    @abstractmethod
    def crawle_and_build_result(self, folders: List[Folder], settings: Sequence[IconSetting], exclude: ExcludeManager):
        pass

    @abstractmethod
    def delete_content(self):
        pass
