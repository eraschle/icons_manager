from typing import Iterable, Protocol

from icon_manager.interfaces.controller import ILibraryController
from icon_manager.rules.manager import ExcludeManager


class IConfigService(ILibraryController):

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

    def set_exclude_manager(self, exclude: ExcludeManager):
        ...

    def find_and_apply_matches(self):
        ...

    def find_existing_content(self):
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

    def find_and_apply_matches(self, overwrite: bool):
        ...

    def find_existing_content(self):
        ...

    def re_apply_matched_icons(self):
        ...

    def delete_icon_settings(self):
        ...
