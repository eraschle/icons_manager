import pytest
from unittest.mock import Mock, patch, MagicMock
from icon_manager.services.config_service import ConfigService
from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.library.controller import IconLibraryController
from icon_manager.rules.manager import ExcludeManager
from icon_manager.interfaces.path import Folder


class TestConfigService:
    
    @pytest.fixture
    def mock_user_config(self):
        config = Mock(spec=UserConfig)
        config.name = 'test_config'
        config.icons_path = '/test/icons'
        config.search_folders = ['/test/search1', '/test/search2']
        config.before_or_after = ['before', 'after']
        return config
    
    @pytest.fixture
    def mock_settings(self):
        return Mock(spec=IconLibraryController)
    
    @pytest.fixture
    def mock_desktop(self):
        return Mock(spec=DesktopIniController)
    
    @pytest.fixture
    def mock_icon_folders(self):
        return Mock(spec=IconFolderController)
    
    @pytest.fixture
    def mock_icon_files(self):
        return Mock(spec=IconFileController)
    
    @pytest.fixture
    def mock_rules(self):
        return Mock(spec=RulesApplyController)
    
    @pytest.fixture
    def config_service(self, mock_user_config, mock_settings, mock_desktop, 
                      mock_icon_folders, mock_icon_files, mock_rules):
        return ConfigService(
            mock_user_config, mock_settings, mock_desktop,
            mock_icon_folders, mock_icon_files, mock_rules
        )

    def test_init_creates_service_with_all_dependencies(self, mock_user_config, mock_settings,
                                                       mock_desktop, mock_icon_folders, 
                                                       mock_icon_files, mock_rules):
        service = ConfigService(
            mock_user_config, mock_settings, mock_desktop,
            mock_icon_folders, mock_icon_files, mock_rules
        )
        
        assert service.user_config == mock_user_config
        assert service.settings == mock_settings
        assert service.desktop == mock_desktop
        assert service.icon_folders == mock_icon_folders
        assert service.icon_files == mock_icon_files
        assert service.rules == mock_rules
        assert service._ConfigService__exclude is None
        assert service._before_or_after == set()

    def test_exclude_property_raises_error_when_not_set(self, config_service):
        with pytest.raises(ValueError, match="has not been set or is None"):
            _ = config_service.exclude

    def test_exclude_property_returns_manager_when_set(self, config_service):
        mock_exclude = Mock(spec=ExcludeManager)
        config_service._ConfigService__exclude = mock_exclude
        
        assert config_service.exclude == mock_exclude

    @patch('icon_manager.services.config_service.crawling_icons')
    def test_create_settings_crawls_icons_and_creates_settings(self, mock_crawling, config_service):
        mock_content = ['icon1.ico', 'icon2.ico']
        mock_crawling.return_value = mock_content
        
        with patch.object(IconLibraryController, 'icons_extensions', ['.ico', '.png']):
            config_service.create_settings()
            
            mock_crawling.assert_called_once_with('/test/icons', ['.ico', '.png'])
            config_service.settings.create_settings.assert_called_once_with(mock_content)

    def test_create_icon_configs_delegates_to_settings(self, config_service):
        config_service.create_icon_configs()
        
        config_service.settings.create_icon_configs.assert_called_once()

    def test_update_icon_configs_delegates_to_settings(self, config_service):
        config_service.update_icon_configs()
        
        config_service.settings.update_icon_configs.assert_called_once()

    def test_delete_icon_configs_delegates_to_settings(self, config_service):
        config_service.delete_icon_configs()
        
        config_service.settings.delete_icon_configs.assert_called_once()

    def test_archive_library_delegates_to_settings(self, config_service):
        config_service.archive_library()
        
        config_service.settings.archive_library.assert_called_once()

    def test_update_before_and_after_merges_configs(self, config_service):
        app_before_after = ['global1', 'global2']
        
        config_service.update_before_and_after(app_before_after)
        
        expected = {'global1', 'global2', 'before', 'after'}
        assert config_service._before_or_after == expected

    def test_set_exclude_manager_configures_and_sets_manager(self, config_service):
        mock_exclude = Mock(spec=ExcludeManager)
        config_service._before_or_after = {'before', 'after'}
        
        config_service.set_exclude_manager(mock_exclude)
        
        mock_exclude.setup_rules.assert_called_once_with({'before', 'after'})
        mock_exclude.clean_empty.assert_called_once()
        assert config_service._ConfigService__exclude == mock_exclude

    @patch('icon_manager.services.config_service.async_crawling_folders')
    def test_crawling_search_folders_crawls_user_folders(self, mock_async_crawling, config_service):
        mock_folders = [Mock(spec=Folder), Mock(spec=Folder)]
        mock_async_crawling.return_value = mock_folders
        
        result = config_service.crawling_search_folders()
        
        mock_async_crawling.assert_called_once_with(['/test/search1', '/test/search2'])
        assert result == mock_folders

    @patch('icon_manager.services.config_service.async_crawling_folders')
    def test_find_and_apply_matches_executes_full_workflow(self, mock_async_crawling, config_service):
        # Setup mocks
        mock_folders = [Mock(spec=Folder)]
        mock_settings = ['setting1', 'setting2']
        mock_filtered_entries = [Mock(spec=Folder)]
        mock_exclude = Mock(spec=ExcludeManager)
        
        mock_async_crawling.return_value = mock_folders
        config_service.settings.create_icon_settings.return_value = mock_settings
        config_service.rules.crawle_and_build_result.return_value = mock_filtered_entries
        config_service._ConfigService__exclude = mock_exclude
        config_service._before_or_after = {'before', 'after'}
        
        config_service.find_and_apply_matches()
        
        # Verify workflow execution
        config_service.settings.create_icon_settings.assert_called_once_with({'before', 'after'})
        mock_async_crawling.assert_called_once_with(['/test/search1', '/test/search2'])
        config_service.rules.crawle_and_build_result.assert_called_once_with(mock_folders, mock_exclude)
        config_service.rules.search_and_find_matches.assert_called_once_with(mock_filtered_entries, mock_settings)
        config_service.rules.creating_found_matches.assert_called_once_with(mock_exclude)

    @patch('icon_manager.services.config_service.async_crawling_folders')
    def test_find_existing_content_crawls_and_builds_content(self, mock_async_crawling, config_service):
        mock_folders = [Mock(spec=Folder)]
        mock_settings = ['setting1', 'setting2']
        
        mock_async_crawling.return_value = mock_folders
        config_service.settings.settings.return_value = mock_settings
        
        config_service.find_existing_content()
        
        mock_async_crawling.assert_called_once_with(['/test/search1', '/test/search2'])
        config_service.settings.settings.assert_called_once_with(clean_empty=True)
        config_service.desktop.crawle_and_build_result.assert_called_once_with(mock_folders, mock_settings)
        config_service.icon_folders.crawle_and_build_result.assert_called_once_with(mock_folders, mock_settings)
        config_service.icon_files.crawle_and_build_result.assert_called_once_with(mock_folders, mock_settings)

    @patch('icon_manager.services.config_service.ReApplyController')
    def test_re_apply_icons_creates_controller_and_re_applies(self, mock_re_apply_controller, config_service):
        mock_controller_instance = Mock()
        mock_re_apply_controller.return_value = mock_controller_instance
        
        config_service.re_apply_icons()
        
        mock_re_apply_controller.assert_called_once_with(config_service.settings, config_service.icon_folders)
        config_service.rules.re_apply_matches.assert_called_once_with(mock_controller_instance)

    def test_delete_content_deletes_from_all_controllers(self, config_service):
        config_service.delete_content()
        
        config_service.desktop.delete_content.assert_called_once()
        config_service.icon_folders.delete_content.assert_called_once()
        config_service.icon_files.delete_content.assert_called_once()

    def test_integration_workflow_with_exclude_manager(self, config_service):
        # Test complete workflow integration
        mock_exclude = Mock(spec=ExcludeManager)
        
        # Setup exclude manager
        config_service.update_before_and_after(['global'])
        config_service.set_exclude_manager(mock_exclude)
        
        # Verify exclude manager is properly configured
        assert config_service.exclude == mock_exclude
        mock_exclude.setup_rules.assert_called_once_with({'global', 'before', 'after'})
        mock_exclude.clean_empty.assert_called_once()

    def test_before_or_after_accumulates_values(self, config_service):
        config_service.update_before_and_after(['first'])
        config_service.update_before_and_after(['second', 'third'])
        
        expected = {'first', 'second', 'third', 'before', 'after'}
        assert config_service._before_or_after == expected