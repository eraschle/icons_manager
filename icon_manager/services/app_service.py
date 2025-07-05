import logging

from icon_manager.config.app import AppConfig
from icon_manager.services.base import IServiceProtocol
from icon_manager.services.configuration_service import ConfigurationService
from icon_manager.services.content_processing_service import ContentProcessingService
from icon_manager.services.library_management_service import LibraryManagementService

log = logging.getLogger(__name__)


class IconsAppService(IServiceProtocol):
    """Orchestrator service that coordinates focused services for icon management.

    This service acts as a facade, delegating work to specialized services:
    - ConfigurationService: Service setup and configuration
    - LibraryManagementService: Library configuration management
    - ContentProcessingService: Content processing and icon application
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

        # Initialize focused services
        self.configuration_service = ConfigurationService(config)
        self._library_service: LibraryManagementService | None = None
        self._content_service: ContentProcessingService | None = None

    def setup(self):
        """Setup all services and initialize service dependencies."""
        self.configuration_service.setup_services()
        services = self.configuration_service.get_services()

        # Initialize dependent services
        self._library_service = LibraryManagementService(services)
        self._content_service = ContentProcessingService(services)

    @property
    def library_service(self) -> LibraryManagementService:
        """Get the library management service."""
        if self._library_service is None:
            raise ValueError("LibraryManagementService has not been initialized.")
        return self._library_service

    @property
    def content_service(self) -> ContentProcessingService:
        """Get the content processing service."""
        if self._content_service is None:
            raise ValueError("ContentProcessingService has not been initialized.")
        return self._content_service

    def create_settings(self):
        """Create icon settings for all services."""
        self.configuration_service.create_settings()

    def create_library_configs(self):
        """Create library configurations."""
        self.library_service.create_configs()

    def update_library_configs(self):
        """Update existing library configurations."""
        self.library_service.update_configs()

    def delete_library_configs(self):
        """Delete library configurations."""
        self.library_service.delete_configs()

    def archive_icons_and_configs(self):
        """Archive unused library configurations."""
        self.library_service.archive_configs()

    def setup_and_merge_user_service(self):
        """Setup and merge user service configurations."""
        self.configuration_service.setup_and_merge_user_service()

    def find_and_apply_matches(self):
        """Find and apply icon matches."""
        self.content_service.find_and_apply_matches()

    def async_find_and_apply_matches(self):
        """Find and apply icon matches asynchronously."""
        self.content_service.async_find_and_apply_matches()

    def find_existing_content(self):
        """Find existing content."""
        self.content_service.find_existing_content()

    def async_find_existing_content(self):
        """Find existing content asynchronously."""
        self.content_service.async_find_existing_content()

    def re_apply_matched_icons(self):
        """Re-apply previously matched icons."""
        self.content_service.re_apply_matched_icons()

    def delete_icon_settings(self):
        """Delete icon settings."""
        self.content_service.delete_icon_settings()

    def async_delete_icon_settings(self):
        """Delete icon settings asynchronously."""
        self.content_service.async_delete_icon_settings()
