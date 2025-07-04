import logging
from collections.abc import Iterable, Sequence
from typing import Protocol

from icon_manager.interfaces.path import File
from icon_manager.library.models import IconFile, IconSetting

log = logging.getLogger(__name__)


class IConfigHandler(Protocol):
    """Protocol for configuration handling operations.

    This protocol defines the interface for components that handle
    configuration creation, updates, and lifecycle management.
    """

    def create_settings(self, content: dict[str, list[File]]) -> None:
        """Create settings from content dictionary.

        Args:
            content: Dictionary mapping file extensions to file lists.

        Note:
            This method should process the content and create appropriate
            internal settings structures.
        """
        ...

    def create_icon_configs(self) -> None:
        """Create configuration files for icons that don't have them.

        This method should scan for icons without configuration files
        and create template configurations for them.
        """
        ...

    def update_icon_configs(self) -> None:
        """Update all icon configuration files with template data.

        This method should apply template updates to existing
        configuration files to ensure they have the latest structure.
        """
        ...

    def delete_icon_configs(self) -> None:
        """Delete all icon configuration files.

        This method should remove all configuration files associated
        with the current icon settings.
        """
        ...

    def archive_library(self) -> None:
        """Archive empty settings in the library.

        This method should identify empty or unused settings and
        move their associated files to an archive location.
        """
        ...


class ISettingsHandler(Protocol):
    """Protocol for settings management operations.

    This protocol defines the interface for components that handle
    settings retrieval, configuration, and icon-specific operations.
    """

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        """Get icon settings with optional filtering.

        Args:
            clean_empty: Whether to filter out empty settings.

        Returns:
            Sequence of IconSetting instances. If clean_empty is True,
            empty settings are excluded from the result.
        """
        ...

    def create_icon_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        """Create icon settings with before/after configuration.

        Args:
            before_or_after: Iterable of before/after settings that should
                           be applied to the icon settings.

        Returns:
            Sequence of configured IconSetting instances with the
            before/after configuration applied.
        """
        ...

    def setting_by_icon(self, icon: IconFile) -> IconSetting | None:
        """Find setting by icon file.

        Args:
            icon: Icon file to find setting for.

        Returns:
            IconSetting instance if found, None if no matching setting exists.
        """
        ...

    def create_settings(self, content: dict[str, list[File]]) -> None:
        """Create settings from content dictionary.

        Args:
            content: Dictionary mapping file extensions to file lists.

        Note:
            This method should process the content and create appropriate
            internal settings structures. This method signature appears
            to be duplicated from IConfigHandler and may need review.
        """
        ...
