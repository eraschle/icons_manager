from typing import Iterable, Protocol

from icon_manager.interfaces.controller import (IContentController,
                                                ILibraryController)
from icon_manager.rules.config import ExcludeRuleConfig


class IConfigService(ILibraryController, IContentController):

    def create_settings(self):
        ...

    def create_icon_configs(self):
        ...

    def update_icon_configs(self):
        ...

    def delete_icon_configs(self):
        ...

    def archive_library(self):
        ...

    def update_before_and_after(self, before_and_after: Iterable[str]):
        ...

    def crawl_content(self, find_matches: bool, exclude: ExcludeRuleConfig):
        ...

    def apply_icons(self):
        ...

    def re_apply_icons(self):
        ...

    def delete_content(self):
        ...


class ServiceProtocol(Protocol):

    def create_settings(self):
        ...

    def create_library_configs(self):
        ...

    def update_library_configs(self):
        ...

    def delete_library_configs(self):
        ...

    def archive_icons_and_configs(self):
        ...

    def apply_matched_icons(self, overwrite: bool):
        ...

    def re_apply_matched_icons(self):
        ...

    def delete_icon_settings(self):
        ...
