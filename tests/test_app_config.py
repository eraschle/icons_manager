import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from icon_manager.config.app import AppConfig, AppConfigFactory, AppConfigs
from icon_manager.config.user import UserConfig
from icon_manager.rules.manager import ExcludeManager
from icon_manager.data.json_source import JsonSource
from icon_manager.rules.factory.manager import ExcludeManagerFactory
from icon_manager.interfaces.path import ConfigFile


class TestAppConfig:
    
    def test_init_creates_config_with_required_params(self):
        user_configs = [Mock(spec=UserConfig)]
        exclude_rules = Mock(spec=ExcludeManager)
        before_or_after = ['before', 'after']
        
        config = AppConfig(user_configs, exclude_rules, before_or_after)
        
        assert config.user_configs == user_configs
        assert config.before_or_after == before_or_after
        assert config._exclude_rules == exclude_rules

    def test_create_exclude_rules_returns_deep_copy(self):
        user_configs = [Mock(spec=UserConfig)]
        exclude_rules = Mock(spec=ExcludeManager)
        before_or_after = ['before']
        
        config = AppConfig(user_configs, exclude_rules, before_or_after)
        
        with patch('icon_manager.config.app.copy.deepcopy') as mock_deepcopy:
            mock_deepcopy.return_value = Mock(spec=ExcludeManager)
            result = config.create_exclude_rules()
            
            mock_deepcopy.assert_called_once_with(exclude_rules)
            assert result == mock_deepcopy.return_value

    def test_validate_calls_validate_on_all_user_configs(self):
        user_config1 = Mock(spec=UserConfig)
        user_config2 = Mock(spec=UserConfig)
        user_configs = [user_config1, user_config2]
        exclude_rules = Mock(spec=ExcludeManager)
        before_or_after = ['before']
        
        config = AppConfig(user_configs, exclude_rules, before_or_after)
        config.validate()
        
        user_config1.validate.assert_called_once()
        user_config2.validate.assert_called_once()


class TestAppConfigFactory:
    
    @pytest.fixture
    def mock_json_source(self):
        return Mock(spec=JsonSource)
    
    @pytest.fixture
    def mock_exclude_factory(self):
        return Mock(spec=ExcludeManagerFactory)
    
    @pytest.fixture
    def factory(self, mock_json_source, mock_exclude_factory):
        return AppConfigFactory(mock_json_source, mock_exclude_factory)

    def test_app_config_path_creates_directory_if_not_exists(self):
        test_path = '/test/path'
        
        with patch('icon_manager.config.app.get_converted_env_path') as mock_convert:
            mock_convert.return_value = test_path
            with patch('os.path.isdir') as mock_isdir:
                mock_isdir.return_value = False
                with patch('os.makedirs') as mock_makedirs:
                    with patch('os.path.join') as mock_join:
                        mock_join.return_value = '/test/path/app_config.config'
                        
                        result = AppConfigFactory.app_config_path('%APPDATA%/Icon-Manager')
                        
                        mock_convert.assert_called_once_with('%APPDATA%/Icon-Manager')
                        mock_isdir.assert_called_once_with(test_path)
                        mock_makedirs.assert_called_once_with(test_path)
                        mock_join.assert_called_once_with(test_path, 'app_config.config')
                        assert result == '/test/path/app_config.config'

    def test_app_config_file_returns_config_file_instance(self):
        with patch.object(AppConfigFactory, 'app_config_path') as mock_path:
            mock_path.return_value = '/test/config.config'
            
            result = AppConfigFactory.app_config_file()
            
            assert isinstance(result, ConfigFile)
            assert result.path == '/test/config.config'

    def test_is_user_config_name_returns_true_for_valid_names(self):
        assert AppConfigFactory.is_user_config_name('user_config.config') is True
        assert AppConfigFactory.is_user_config_name('my_config.config') is True

    def test_is_user_config_name_returns_false_for_reserved_names(self):
        assert AppConfigFactory.is_user_config_name('app_config.config') is False
        assert AppConfigFactory.is_user_config_name('excluded_rules.config') is False

    def test_get_user_config_paths_filters_and_returns_paths(self, factory):
        folder_path = '/test/folder'
        
        with patch('icon_manager.config.app.get_files') as mock_get_files:
            mock_get_files.return_value = ['user1.config', 'app_config.config', 'user2.config']
            with patch('icon_manager.config.app.get_paths') as mock_get_paths:
                mock_get_paths.return_value = ['/test/folder/user1.config', '/test/folder/user2.config']
                
                result = AppConfigFactory.get_user_config_paths(folder_path)
                
                mock_get_files.assert_called_once_with(folder_path, '.config')
                mock_get_paths.assert_called_once_with(folder_path, ['user1.config', 'user2.config'])
                assert result == ['/test/folder/user1.config', '/test/folder/user2.config']

    def test_create_user_configs_creates_valid_configs(self, factory):
        content = {AppConfigs.USER_CONFIGS: '/test/folder'}
        
        with patch.object(factory, '_get_user_config_paths') as mock_get_paths:
            mock_get_paths.return_value = ['/test/folder/user1.config', '/test/folder/user2.config']
            
            mock_user_config1 = Mock(spec=UserConfig)
            mock_user_config1.has_search_folders.return_value = True
            mock_user_config2 = Mock(spec=UserConfig)
            mock_user_config2.has_search_folders.return_value = True
            
            factory.user_factory = Mock()
            factory.user_factory.create.side_effect = [mock_user_config1, mock_user_config2]
            
            result = factory.create_user_configs(content)
            
            assert len(result) == 2
            assert result[0] == mock_user_config1
            assert result[1] == mock_user_config2

    def test_create_user_configs_skips_invalid_configs(self, factory):
        content = {AppConfigs.USER_CONFIGS: '/test/folder'}
        
        with patch.object(factory, '_get_user_config_paths') as mock_get_paths:
            mock_get_paths.return_value = ['/test/folder/user1.config', '/test/folder/user2.config']
            
            mock_user_config1 = Mock(spec=UserConfig)
            mock_user_config1.has_search_folders.return_value = True
            mock_user_config2 = Mock(spec=UserConfig)
            mock_user_config2.has_search_folders.return_value = False
            
            factory.user_factory = Mock()
            factory.user_factory.create.side_effect = [mock_user_config1, mock_user_config2]
            
            result = factory.create_user_configs(content)
            
            assert len(result) == 1
            assert result[0] == mock_user_config1

    def test_create_exclude_config_returns_manager_when_config_exists(self, factory):
        content = {AppConfigs.USER_CONFIGS: '/test/folder'}
        mock_exclude_manager = Mock(spec=ExcludeManager)
        
        with patch.object(factory, '_get_exclude_config_path') as mock_get_path:
            mock_get_path.return_value = '/test/folder/excluded_rules.config'
            factory.excluded_factory = Mock()
            factory.excluded_factory.create.return_value = mock_exclude_manager
            
            result = factory.create_exclude_config(content)
            
            assert result == mock_exclude_manager

    def test_create_exclude_config_returns_empty_manager_when_no_config(self, factory):
        content = {AppConfigs.USER_CONFIGS: '/test/folder'}
        
        with patch.object(factory, '_get_exclude_config_path') as mock_get_path:
            mock_get_path.return_value = None
            
            result = factory.create_exclude_config(content)
            
            assert isinstance(result, ExcludeManager)
            assert result.checkers == []

    def test_create_raises_error_when_no_valid_user_configs(self, factory):
        mock_file = Mock(spec=ConfigFile)
        mock_file.exists.return_value = True
        
        factory.source.read.return_value = {AppConfigs.USER_CONFIGS: '/test/folder'}
        
        with patch.object(factory, 'does_user_config_path_exists') as mock_path_exists:
            mock_path_exists.return_value = True
            with patch.object(factory, 'does_user_configs_exists') as mock_configs_exist:
                mock_configs_exist.return_value = True
                with patch.object(factory, 'create_user_configs') as mock_create_users:
                    mock_create_users.return_value = []
                    with patch.object(factory, 'create_exclude_config') as mock_create_exclude:
                        mock_create_exclude.return_value = Mock(spec=ExcludeManager)
                        
                        with pytest.raises(ValueError, match="No valid user configuration exists"):
                            factory.create(mock_file)

    def test_create_successful_creation(self, factory):
        mock_file = Mock(spec=ConfigFile)
        mock_file.exists.return_value = True
        
        mock_user_config = Mock(spec=UserConfig)
        mock_exclude_manager = Mock(spec=ExcludeManager)
        
        factory.source.read.return_value = {
            AppConfigs.USER_CONFIGS: '/test/folder',
            AppConfigs.BEFORE_OR_AFTER: ['before', 'after']
        }
        
        with patch.object(factory, 'does_user_config_path_exists') as mock_path_exists:
            mock_path_exists.return_value = True
            with patch.object(factory, 'does_user_configs_exists') as mock_configs_exist:
                mock_configs_exist.return_value = True
                with patch.object(factory, 'create_user_configs') as mock_create_users:
                    mock_create_users.return_value = [mock_user_config]
                    with patch.object(factory, 'create_exclude_config') as mock_create_exclude:
                        mock_create_exclude.return_value = mock_exclude_manager
                        factory.source.write = Mock()
                        
                        result = factory.create(mock_file)
                        
                        assert isinstance(result, AppConfig)
                        assert result.user_configs == [mock_user_config]
                        assert result.before_or_after == ['before', 'after']
                        assert result._exclude_rules == mock_exclude_manager