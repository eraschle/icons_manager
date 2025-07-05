from typing import Iterable, Protocol

from icon_manager.config.user import UserConfig
from icon_manager.interfaces.controller import IConfigHandler
from icon_manager.rules.manager import ExcludeManager


class IConfigService(IConfigHandler):
    user_config: UserConfig

    def create_icon_settings(self):
        """
        Create and initialize icon-related settings for the configuration service.
        """
        ...

    def create_icon_configs(self):
        """
        Create new icon configuration entries.
        
        Returns:
            The created icon configuration objects or data structure.
        """
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
        """
        Assigns an ExcludeManager to control which items are excluded from icon configuration operations.
        
        Parameters:
            exclude (ExcludeManager): The manager responsible for handling exclusion logic.
        """
        ...

    def find_and_apply(self):
        """
        Finds relevant icon configurations and applies them as needed.
        """
        ...

    def find_existing(self):
        """
        Locate and return existing icon-related configurations or settings.
        
        Returns:
            The existing icon configurations or settings found, or None if none are present.
        """
        ...

    def re_apply_icons(self):
        """
        Reapplies icon configurations or settings, typically to refresh or update their application state.
        """
        ...

    def delete_setting(self):
        """
        Delete the current icon-related setting or configuration from the service.
        """
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
