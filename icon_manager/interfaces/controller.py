import logging
from typing import Dict, List, Protocol, Sequence

from icon_manager.helpers.path import File, Folder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class ILibraryController(Protocol):

    def create_settings(self, content: Dict[str, List[File]]):
        ...

    def create_icon_configs(self):
        ...

    def update_icon_configs(self):
        ...

    def delete_icon_configs(self):
        ...

    def archive_library(self):
        ...


class IContentController(Protocol):

    def crawl_content(self, folders: List[Folder], settings: Sequence[IconSetting]):
        ...

    def delete_content(self):
        ...
