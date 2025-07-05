from typing import Iterable, Protocol

from icon_manager.config.user import UserConfig
from icon_manager.interfaces.controller import IConfigHandler
from icon_manager.rules.manager import ExcludeManager

"""Base service interfaces for icon management operations.

This module defines the core protocols and interfaces used by the icon manager
services. It provides contracts for configuration management, library operations,
and content processing services.

The protocols defined here ensure consistent interfaces across different service
implementations and enable proper dependency injection and testing.
"""


class IConfigService(IConfigHandler, Protocol):
    """Service interface for configuration management and icon operations.
    
    This protocol defines the contract for services that handle icon configuration,
    library management, and content processing operations.
    """
    user_config: UserConfig

    def create_icon_settings(self):
        """Create new icon settings based on current configuration."""
        ...

    def create_icon_configs(self):
        """Create icon configuration files."""
        ...

    def update_icon_configs(self):
        """Update existing icon configuration files."""
        ...

    def delete_icon_configs(self):
        """Delete icon configuration files."""
        ...

    def archive_library(self):
        """Archive the current icon library."""
        ...

    def update_before_and_after(self, before_and_after: Iterable[str]):
        """Update before and after processing states.
        
        Args:
            before_and_after: Iterable of state information strings.
        """
        ...

    def set_exclude_manager(self, exclude: ExcludeManager):
        """Set the exclude manager for filtering operations.
        
        Args:
            exclude: ExcludeManager instance for handling exclusion rules.
        """
        ...

    def find_and_apply(self):
        """Find matching icons and apply them to folders."""
        ...

    def find_existing(self):
        """Find existing icon configurations and content."""
        ...

    def re_apply_icons(self):
        """Re-apply previously matched icons to their folders."""
        ...

    def delete_setting(self):
        """Delete icon settings and configurations."""
        ...


class IServiceProtocol(Protocol):
    """Main service protocol for icon management operations.
    
    This protocol defines the high-level interface for the main application service
    that orchestrates all icon management operations including library management,
    content processing, and configuration handling.
    """

    def create_settings(self):
        """Create initial settings and configuration for the icon manager."""
        ...

    def create_library_configs(self):
        """Create configuration files for the icon library."""
        ...

    def update_library_configs(self):
        """Update existing icon library configuration files."""
        ...

    def delete_library_configs(self):
        """Delete icon library configuration files."""
        ...

    def archive_icons_and_configs(self):
        """Archive both icons and their associated configuration files."""
        ...

    def find_and_apply_matches(self):
        """Find folders that match icon rules and apply appropriate icons."""
        ...

    def find_existing_content(self):
        """Scan for existing icon content and configurations."""
        ...

    def re_apply_matched_icons(self):
        """Re-apply icons to folders that were previously matched."""
        ...

    def delete_icon_settings(self):
        """Remove all icon settings and clean up associated files."""
        ...
