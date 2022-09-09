import logging
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

from icon_manager.helpers.path import File
from icon_manager.library.models import IconFile, IconSetting

log = logging.getLogger(__name__)


class IConfigHandler(Protocol):

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


class ISettingsHandler(Protocol):

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        ...

    def create_icon_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        ...

    def setting_by_icon(self, icon: IconFile) -> Optional[IconSetting]:
        ...

    def create_settings(self, content: Dict[str, List[File]]):
        ...
