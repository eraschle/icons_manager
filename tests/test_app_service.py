import pytest
from unittest.mock import Mock
from icon_manager.services.app_service import IconsAppService
from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.services.config_service import ConfigService


class TestIconsAppService:
    
    @pytest.fixture
    def mock_app_config(self):
        config = Mock(spec=AppConfig)
        config.user_configs = []
        config.before_or_after = ['before', 'after']
        config.create_exclude_rules.return_value = Mock()
        return config
    
    @pytest.fixture
    def service(self, mock_app_config):
        return IconsAppService(mock_app_config)

    def test_init_creates_service_with_config(self, mock_app_config):
        service = IconsAppService(mock_app_config)
        
        assert service.config == mock_app_config
        assert service.services == []

    def test_setup_creates_services_for_each_user_config(self, mock_app_config):
        user_config1 = Mock(spec=UserConfig)
        user_config2 = Mock(spec=UserConfig)
        mock_app_config.user_configs = [user_config1, user_config2]
        
        service = IconsAppService(mock_app_config)
        service.setup()
        
        assert len(service.services) == 2
        assert all(isinstance(s, ConfigService) for s in service.services)

    def test_create_service_returns_config_service_with_controllers(self, service):
        user_config = Mock(spec=UserConfig)
        
        config_service = service._create_service(user_config)
        
        assert isinstance(config_service, ConfigService)
        assert config_service.user_config == user_config

    def test_create_settings_calls_create_settings_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.create_settings()
        
        mock_service1.create_settings.assert_called_once()
        mock_service2.create_settings.assert_called_once()

    def test_create_library_configs_calls_create_icon_configs_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.create_library_configs()
        
        mock_service1.create_icon_configs.assert_called_once()
        mock_service2.create_icon_configs.assert_called_once()

    def test_update_library_configs_calls_update_icon_configs_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.update_library_configs()
        
        mock_service1.update_icon_configs.assert_called_once()
        mock_service2.update_icon_configs.assert_called_once()

    def test_delete_library_configs_calls_delete_icon_configs_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.delete_library_configs()
        
        mock_service1.delete_icon_configs.assert_called_once()
        mock_service2.delete_icon_configs.assert_called_once()

    def test_archive_icons_and_configs_calls_archive_library_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.archive_icons_and_configs()
        
        mock_service1.archive_library.assert_called_once()
        mock_service2.archive_library.assert_called_once()

    def test_setup_and_merge_user_service_configures_services_properly(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.setup_and_merge_user_service()
        
        mock_service1.update_before_and_after.assert_called_once_with(['before', 'after'])
        mock_service2.update_before_and_after.assert_called_once_with(['before', 'after'])
        mock_service1.set_exclude_manager.assert_called_once()
        mock_service2.set_exclude_manager.assert_called_once()

    def test_find_and_apply_matches_calls_find_and_apply_matches_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.find_and_apply_matches()
        
        mock_service1.find_and_apply_matches.assert_called_once()
        mock_service2.find_and_apply_matches.assert_called_once()

    def test_find_existing_content_calls_find_existing_content_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.find_existing_content()
        
        mock_service1.find_existing_content.assert_called_once()
        mock_service2.find_existing_content.assert_called_once()

    def test_re_apply_matched_icons_calls_re_apply_icons_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.re_apply_matched_icons()
        
        mock_service1.re_apply_icons.assert_called_once()
        mock_service2.re_apply_icons.assert_called_once()

    def test_delete_icon_settings_calls_delete_content_on_all_services(self, service):
        mock_service1 = Mock(spec=ConfigService)
        mock_service2 = Mock(spec=ConfigService)
        service.services = [mock_service1, mock_service2]
        
        service.delete_icon_settings()
        
        mock_service1.delete_content.assert_called_once()
        mock_service2.delete_content.assert_called_once()