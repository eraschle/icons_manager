import logging
from typing import Dict, Iterable, List, Optional, Protocol, Sequence

from icon_manager.interfaces.path import File
from icon_manager.library.models import IconFile, IconSetting

log = logging.getLogger(__name__)


class IConfigHandler(Protocol):

    def create_icon_settings(self, content: Dict[str, List[File]]):
        """
        Create icon settings from the provided content mapping.
        
        Parameters:
            content (Dict[str, List[File]]): A dictionary mapping identifiers to lists of File objects to be used for icon settings.
        """
        ...

    def create_icon_configs(self):
        """
        Create icon configuration files or entries for the icon library.
        """
        ...

    def update_icon_configs(self):
        ...

    def delete_icon_configs(self):
        ...

    def archive_library(self):
        ...


class ISettingsHandler(Protocol):

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        """
        Retrieve a sequence of icon settings, optionally excluding empty entries.
        
        Parameters:
        	clean_empty (bool): If True, empty settings are removed from the result.
        
        Returns:
        	Sequence[IconSetting]: A list of icon settings, possibly filtered to exclude empty entries.
        """
        ...

    def updated_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        """
        Return updated icon settings filtered by the provided iterable of identifiers.
        
        Parameters:
            before_or_after (Iterable[str]): Identifiers used to filter which icon settings are considered updated.
        
        Returns:
            Sequence[IconSetting]: A sequence of updated icon settings matching the filter criteria.
        """
        ...

    def setting_by_icon(self, icon: IconFile) -> Optional[IconSetting]:
        """
        Retrieve the icon setting associated with the specified icon file.
        
        Parameters:
            icon (IconFile): The icon file for which to find the corresponding setting.
        
        Returns:
            Optional[IconSetting]: The matching icon setting if found, otherwise None.
        """
        ...
