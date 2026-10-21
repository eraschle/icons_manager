import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from icon_manager.config.user import UserConfig
from icon_manager.interfaces.actions import Action
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.interfaces.path import Folder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class ContentController[TModel](ABC):
    """Finds and removes one kind of content this tool writes.

    The three kinds - desktop.ini files, ``__icon__`` folders and the icon
    files copied into them - differ only in what they look for, so each
    subclass supplies a builder and the two operations below.
    """

    def __init__(self, user_config: UserConfig, builder: CrawlerBuilder[TModel]) -> None:
        self.user_config = user_config
        self.builder = builder

    @abstractmethod
    def crawle_and_build_result(self, folders: list[Folder], settings: Sequence[IconSetting]) -> None:
        """Collect this controller's content from an already crawled tree.

        The abstract signature took a third ``exclude`` argument that no
        implementation accepted, so none of them actually overrode it.
        """

    @abstractmethod
    def delete_content(self) -> Action:
        """Delete the collected content, returning the action that did it.

        The action carries the counts that ``@execution_action`` logs, so it
        is returned rather than discarded.
        """
