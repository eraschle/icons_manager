from collections.abc import Iterable
from typing import Protocol

from icon_manager.interfaces.controller import IConfigHandler
from icon_manager.rules.manager import ExcludeManager


class IConfigService(IConfigHandler, Protocol):
    """Protocol for configuration service operations.

    This protocol extends IConfigHandler with additional service-level operations
    for managing the complete icon configuration workflow. It defines methods for
    applying rules, managing exclude filters, and coordinating various icon
    management operations.

    The service acts as the main orchestrator for icon management tasks,
    coordinating between different controllers and managers.
    """

    def update_before_and_after(self, before_and_after: Iterable[str]) -> None:
        """Update before/after configuration values.

        Parameters
        ----------
        before_and_after : Iterable[str]
            Iterable of before/after configuration values that should be
            merged with existing settings.

        Notes
        -----
        These values are typically used for rule filtering and icon
        application timing configuration.
        """
        ...

    def set_exclude_manager(self, exclude: ExcludeManager) -> None:
        """Set the exclude manager for filtering operations.

        Parameters
        ----------
        exclude : ExcludeManager
            ExcludeManager instance that defines which folders and files
            should be excluded from icon operations.

        Notes
        -----
        The exclude manager should be configured with appropriate
        rules before being set on the service.
        """
        ...

    def find_and_apply_matches(self) -> None:
        """Find matching folders and apply icon configurations.

        Notes
        -----
        This method performs the core icon management workflow:

        1. Crawls through configured search directories
        2. Applies exclude rules to filter unwanted folders
        3. Matches folders against icon rules
        4. Creates and applies icon configurations

        This is typically the main operation for applying icons to folders.
        """
        ...

    def find_existing_content(self) -> None:
        """Find and catalog existing icon content.

        Notes
        -----
        This method scans for existing desktop.ini files, icon folders,
        and icon files that were previously created by the icon manager.
        It builds internal catalogs of existing content for management
        operations like cleanup or re-application.
        """
        ...

    def re_apply_icons(self) -> None:
        """Re-apply icons to previously configured folders.

        Notes
        -----
        This method finds folders that already have icon configurations
        and re-applies the icon settings. Useful for updating existing
        configurations after rule or icon changes.
        """
        ...

    def delete_content(self) -> None:
        """Delete all icon-related content.

        Notes
        -----
        This method removes all desktop.ini files, icon folders, and
        icon files that were created by the icon manager. It effectively
        cleans up all traces of icon management from the file system.
        """
        ...


class IServiceProtocol(Protocol):
    """Protocol for high-level service operations.

    This protocol defines the interface for application-level services
    that coordinate multiple configuration services. It provides methods
    for batch operations across multiple user configurations and manages
    the overall application workflow.

    Implementations typically manage collections of IConfigService instances
    and coordinate operations across them.
    """

    def create_settings(self) -> None:
        """Create settings for all managed configurations.

        Notes
        -----
        This method initializes settings for all user configurations
        managed by the service. It typically delegates to individual
        configuration services to create their respective settings.
        """
        ...

    def create_library_configs(self) -> None:
        """Create library configuration files.

        Notes
        -----
        This method creates configuration templates and files for
        the icon library across all managed configurations. It ensures
        that all necessary configuration files exist for proper operation.
        """
        ...

    def update_library_configs(self) -> None:
        """Update existing library configuration files.

        Notes
        -----
        This method applies updates to existing library configuration
        files to ensure they have the latest structure and settings.
        Useful when the application configuration format changes.
        """
        ...

    def delete_library_configs(self) -> None:
        """Delete all library configuration files.

        Notes
        -----
        This method removes all library configuration files across
        all managed configurations. Used for cleanup or reset operations.
        """
        ...

    def archive_icons_and_configs(self) -> None:
        """Archive unused icons and configuration files.

        Notes
        -----
        This method identifies unused or empty icon configurations
        and moves them to archive locations. Helps maintain a clean
        library by removing unused resources.
        """
        ...

    def find_and_apply_matches(self, overwrite: bool) -> None:
        """Find and apply icon matches across all configurations.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing icon configurations.
            If True, existing configurations will be replaced.
            If False, existing configurations will be preserved.

        Notes
        -----
        This method coordinates the icon application process across
        all managed user configurations, applying the specified
        overwrite policy consistently.
        """
        ...

    def find_existing_content(self) -> None:
        """Find existing icon content across all configurations.

        Notes
        -----
        This method scans for existing icon-related content across
        all managed user configurations. It builds a comprehensive
        catalog of existing desktop.ini files, icon folders, and
        icon files for management purposes.
        """
        ...

    def re_apply_matched_icons(self) -> None:
        """Re-apply icons to previously matched folders.

        Notes
        -----
        This method re-applies icon configurations to folders that
        were previously processed by the icon manager. Useful for
        refreshing configurations after icon library updates or
        rule changes across all managed configurations.
        """
        ...

    def delete_icon_settings(self) -> None:
        """Delete all icon settings and related content.

        Notes
        -----
        This method performs a comprehensive cleanup by removing
        all icon-related settings, files, and configurations across
        all managed user configurations. It effectively resets the
        system to a clean state.
        """
        ...
