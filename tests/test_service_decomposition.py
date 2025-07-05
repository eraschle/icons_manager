import pytest
from unittest.mock import Mock, patch

from icon_manager.config.app import AppConfig
from icon_manager.services.app_service import IconsAppService
from icon_manager.services.library_management_service import LibraryManagementService
from icon_manager.services.content_processing_service import ContentProcessingService
from icon_manager.services.configuration_service import ConfigurationService


class TestServiceDecomposition:
    """Test the service decomposition and new focused services."""
    
    @pytest.fixture
    def mock_app_config(self):
        """Create a mock AppConfig for testing."""
        config = Mock(spec=AppConfig)
        config.user_configs = []
        config.before_or_after = []
        return config
    
    def test_icons_app_service_uses_focused_services(self, mock_app_config):
        """Test that IconsAppService properly uses the new focused services."""
        app_service = IconsAppService(mock_app_config)
        
        # Verify focused services are created
        assert isinstance(app_service.configuration_service, ConfigurationService)
        assert app_service.library_service is None  # Not initialized until setup()
        assert app_service.content_service is None  # Not initialized until setup()
    
    @patch('icon_manager.services.configuration_service.ConfigurationService.setup_services')
    @patch('icon_manager.services.configuration_service.ConfigurationService.get_services')
    def test_setup_initializes_dependent_services(self, mock_get_services, mock_setup_services, mock_app_config):
        """Test that setup() properly initializes dependent services."""
        mock_services = [Mock(), Mock()]
        mock_get_services.return_value = mock_services
        
        app_service = IconsAppService(mock_app_config)
        app_service.setup()
        
        # Verify setup was called
        mock_setup_services.assert_called_once()
        mock_get_services.assert_called_once()
        
        # Verify dependent services are initialized
        assert isinstance(app_service.library_service, LibraryManagementService)
        assert isinstance(app_service.content_service, ContentProcessingService)
        assert app_service.library_service.services == mock_services
        assert app_service.content_service.services == mock_services
    
    def test_library_management_service_delegation(self, mock_app_config):
        """Test that library operations are properly delegated."""
        app_service = IconsAppService(mock_app_config)
        app_service.library_service = Mock(spec=LibraryManagementService)
        
        # Test delegation
        app_service.create_library_configs()
        app_service.library_service.create_configs.assert_called_once()
        
        app_service.update_library_configs()
        app_service.library_service.update_configs.assert_called_once()
        
        app_service.delete_library_configs()
        app_service.library_service.delete_configs.assert_called_once()
        
        app_service.archive_icons_and_configs()
        app_service.library_service.archive_configs.assert_called_once()
    
    def test_content_processing_service_delegation(self, mock_app_config):
        """Test that content processing operations are properly delegated."""
        app_service = IconsAppService(mock_app_config)
        app_service.content_service = Mock(spec=ContentProcessingService)
        
        # Test delegation
        app_service.find_and_apply_matches()
        app_service.content_service.find_and_apply_matches.assert_called_once()
        
        app_service.async_find_and_apply_matches()
        app_service.content_service.async_find_and_apply_matches.assert_called_once()
        
        app_service.find_existing_content()
        app_service.content_service.find_existing_content.assert_called_once()
        
        app_service.re_apply_matched_icons()
        app_service.content_service.re_apply_matched_icons.assert_called_once()
    
    def test_configuration_service_delegation(self, mock_app_config):
        """Test that configuration operations are properly delegated."""
        app_service = IconsAppService(mock_app_config)
        
        # Test delegation to configuration service
        app_service.create_settings()
        # This should not raise an error and should call the configuration service
        
        app_service.setup_and_merge_user_service()
        # This should not raise an error and should call the configuration service


class TestLibraryManagementService:
    """Test LibraryManagementService functionality."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        service1 = Mock()
        service2 = Mock()
        return [service1, service2]
    
    def test_create_configs(self, mock_services):
        """Test create_configs delegates to all services."""
        library_service = LibraryManagementService(mock_services)
        library_service.create_configs()
        
        for service in mock_services:
            service.create_icon_configs.assert_called_once()
    
    def test_update_configs(self, mock_services):
        """Test update_configs delegates to all services."""
        library_service = LibraryManagementService(mock_services)
        library_service.update_configs()
        
        for service in mock_services:
            service.update_icon_configs.assert_called_once()
    
    def test_delete_configs(self, mock_services):
        """Test delete_configs delegates to all services."""
        library_service = LibraryManagementService(mock_services)
        library_service.delete_configs()
        
        for service in mock_services:
            service.delete_icon_configs.assert_called_once()
    
    def test_archive_configs(self, mock_services):
        """Test archive_configs delegates to all services."""
        library_service = LibraryManagementService(mock_services)
        library_service.archive_configs()
        
        for service in mock_services:
            service.archive_library.assert_called_once()


class TestContentProcessingService:
    """Test ContentProcessingService functionality."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        service1 = Mock()
        service2 = Mock()
        return [service1, service2]
    
    def test_find_and_apply_matches(self, mock_services):
        """Test find_and_apply_matches delegates to all services."""
        content_service = ContentProcessingService(mock_services)
        content_service.find_and_apply_matches()
        
        for service in mock_services:
            service.find_and_apply.assert_called_once()
    
    def test_find_existing_content(self, mock_services):
        """Test find_existing_content delegates to all services."""
        content_service = ContentProcessingService(mock_services)
        content_service.find_existing_content()
        
        for service in mock_services:
            service.find_existing.assert_called_once()
    
    def test_re_apply_matched_icons(self, mock_services):
        """Test re_apply_matched_icons delegates to all services."""
        content_service = ContentProcessingService(mock_services)
        content_service.re_apply_matched_icons()
        
        for service in mock_services:
            service.re_apply_icons.assert_called_once()
    
    def test_delete_icon_settings(self, mock_services):
        """Test delete_icon_settings delegates to all services."""
        content_service = ContentProcessingService(mock_services)
        content_service.delete_icon_settings()
        
        for service in mock_services:
            service.delete_setting.assert_called_once()