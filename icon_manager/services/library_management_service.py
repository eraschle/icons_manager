import logging
from typing import List

from icon_manager.services.base import IConfigService

log = logging.getLogger(__name__)


class LibraryManagementService:
    """Focused service for managing icon library configurations.
    
    Responsibilities:
    - Create library configurations
    - Update existing library configurations  
    - Delete library configurations
    - Archive unused configurations
    """
    
    def __init__(self, services: List[IConfigService]) -> None:
        self.services = services
    
    def create_configs(self) -> None:
        """Create library configurations for all services."""
        for service in self.services:
            service.create_icon_configs()
    
    def update_configs(self) -> None:
        """Update existing library configurations for all services."""
        for service in self.services:
            service.update_icon_configs()
    
    def delete_configs(self) -> None:
        """Delete library configurations for all services."""
        for service in self.services:
            service.delete_icon_configs()
    
    def archive_configs(self) -> None:
        """Archive unused library configurations for all services."""
        for service in self.services:
            service.archive_library()