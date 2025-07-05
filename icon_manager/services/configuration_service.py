import logging
from typing import List

from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.library.controller import IconLibraryController
from icon_manager.services.base import IConfigService
from icon_manager.services.config_service import ConfigService

log = logging.getLogger(__name__)


class ConfigurationService:
    """Focused service for configuration management and service setup.
    
    Responsibilities:
    - Setup and configure services
    - Create service instances
    - Manage configuration merging
    - Handle exclude rules setup
    """
    
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.services: List[IConfigService] = []
    
    def setup_services(self) -> None:
        """Setup all services based on user configurations."""
        self.services.clear()
        for user_config in self.config.user_configs:
            service = self._create_service(user_config)
            self.services.append(service)
    
    def _create_service(self, user_config: UserConfig) -> IConfigService:
        """Create a ConfigService instance for the given user configuration."""
        library = IconLibraryController(user_config)
        desktop = DesktopIniController(user_config)
        folders = IconFolderController(user_config)
        files = IconFileController(user_config)
        rules = RulesApplyController(user_config)
        return ConfigService(
            user_config,
            settings=library,
            desktop=desktop,
            icon_folders=folders,
            icon_files=files,
            rules=rules
        )
    
    def create_settings(self) -> None:
        """Create icon settings for all services."""
        for service in self.services:
            service.create_icon_settings()
    
    def setup_and_merge_user_service(self) -> None:
        """Setup and merge user service configurations with exclude rules."""
        for service in self.services:
            service.update_before_and_after(self.config.before_or_after)
            exclude = self.config.create_exclude_rules()
            service.set_exclude_manager(exclude)
    
    def get_services(self) -> List[IConfigService]:
        """Get all configured services."""
        return self.services.copy()