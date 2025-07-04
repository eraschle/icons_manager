from typing import Any
from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from icon_manager.config.user import (
    UserConfig,
    UserConfigFactory,
    UserConfigs,
    get_icons_path,
    get_icons_search_folder,
    get_search_folders,
)
from icon_manager.data.json_source import JsonSource
from icon_manager.interfaces.path import ConfigFile, IconSearchFolder, SearchFolder


class TestUserConfig:
    @pytest.fixture
    def mock_search_folders(self):
        folder1 = Mock(spec=IconSearchFolder)
        folder1.path = "/test/search1"
        folder2 = Mock(spec=IconSearchFolder)
        folder2.path = "/test/search2"
        return [folder1, folder2]

    @pytest.fixture
    def user_config(self, mock_search_folders):
        icons_path = Mock(spec=SearchFolder)
        return UserConfig(
            name="test_config",
            icons_path=icons_path,
            search_folders=mock_search_folders,
            code_folders=["code1", "code2"],
            exclude_folders=["exclude1", "exclude2"],
            before_or_after=["before", "after"],
            copy_icon=True,
        )

    def test_init_creates_config_with_all_properties(self, user_config, mock_search_folders):
        assert user_config.name == "test_config"
        assert user_config.search_folders == mock_search_folders
        assert user_config.code_folders == ["code1", "code2"]
        assert user_config.exclude_folders == ["exclude1", "exclude2"]
        assert user_config.before_or_after == {"before", "after"}
        assert user_config.copy_icon is True
        assert isinstance(user_config.uuid, UUID)

    def test_file_name_returns_config_pattern(self):
        assert UserConfig.file_name() == "*.config"

    def test_validate_sets_filter_globals(self, user_config):
        with patch("icon_manager.config.user.filters") as mock_filters:
            user_config.validate()

            assert mock_filters.EXCLUDED_FOLDERS == ["exclude1", "exclude2"]
            assert mock_filters.PROJECT_FOLDERS == ["code1", "code2"]

    def test_has_search_folders_returns_true_when_folders_exist(self, user_config):
        assert user_config.has_search_folders() is True

    def test_has_search_folders_returns_false_when_no_folders(self):
        icons_path = Mock(spec=SearchFolder)
        config = UserConfig(
            name="test",
            icons_path=icons_path,
            search_folders=[],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )

        assert config.has_search_folders() is False

    def test_search_folder_by_returns_matching_folder(self, user_config, mock_search_folders):
        mock_entry = Mock()
        mock_search_folders[0].is_path_entry.return_value = False
        mock_search_folders[1].is_path_entry.return_value = True

        result = user_config.search_folder_by(mock_entry)

        assert result == mock_search_folders[1]
        mock_search_folders[0].is_path_entry.assert_called_once_with(mock_entry)
        mock_search_folders[1].is_path_entry.assert_called_once_with(mock_entry)

    def test_search_folder_by_raises_error_when_no_match(self, user_config, mock_search_folders):
        mock_entry = Mock()
        mock_entry.path = "/test/unknown"
        mock_search_folders[0].is_path_entry.return_value = False
        mock_search_folders[1].is_path_entry.return_value = False

        with pytest.raises(ValueError, match="Search folder for /test/unknown not exists"):
            user_config.search_folder_by(mock_entry)


class TestGetIconsPath:
    def test_get_icons_path_returns_search_folder(self):
        mock_file = Mock(spec=ConfigFile)
        content: dict[str, Any] = {
            UserConfigs.ICONS_PATH: "/test/icons",
        }

        with patch("icon_manager.config.user.get_converted_env_path") as mock_convert:
            mock_convert.return_value = "/converted/icons"

            result = get_icons_path(mock_file, content)

            mock_convert.assert_called_once_with("/test/icons")
            assert isinstance(result, SearchFolder)
            assert result.path == "/converted/icons"

    def test_get_icons_path_raises_error_when_missing(self):
        mock_file = Mock(spec=ConfigFile)
        mock_file.path = "/test/config.json"
        content = {}

        with pytest.raises(ValueError, match="Icon path DOES NOT exists in /test/config.json"):
            get_icons_path(mock_file, content)


class TestGetIconsSearchFolder:
    def test_get_icons_search_folder_creates_folder_with_copy_icon(self):
        content: dict[str, Any] = {
            UserConfigs.SEARCH_PATH: "/test/search",
            UserConfigs.COPY_ICONS: True,
        }

        with patch("icon_manager.config.user.get_converted_env_path") as mock_convert:
            mock_convert.return_value = "/converted/search"

            result = get_icons_search_folder(content)

            mock_convert.assert_called_once_with("/test/search")
            assert isinstance(result, IconSearchFolder)
            assert result.path == "/converted/search"

    def test_get_icons_search_folder_raises_error_when_no_path(self):
        content: dict[str, Any] = {
            UserConfigs.COPY_ICONS: True,
        }

        with pytest.raises(ValueError, match="NO path for search folders found"):
            get_icons_search_folder(content)


class TestGetSearchFolders:
    def test_get_search_folders_returns_valid_folders(self):
        mock_file = Mock(spec=ConfigFile)
        content: dict[str, Any] = {
            UserConfigs.SEARCH_FOLDERS: [
                {
                    UserConfigs.SEARCH_PATH: "/test/search1",
                    UserConfigs.COPY_ICONS: True,
                },
                {
                    UserConfigs.SEARCH_PATH: "/test/search2",
                    UserConfigs.COPY_ICONS: False,
                },
            ]
        }

        with patch("icon_manager.config.user.get_icons_search_folder") as mock_get_folder:
            mock_folder1 = Mock(spec=IconSearchFolder)
            mock_folder1.exists.return_value = True
            mock_folder2 = Mock(spec=IconSearchFolder)
            mock_folder2.exists.return_value = True
            mock_get_folder.side_effect = [mock_folder1, mock_folder2]

            result = get_search_folders(mock_file, content)

            assert len(result) == 2
            assert result[0] == mock_folder1
            assert result[1] == mock_folder2

    def test_get_search_folders_skips_non_existing_folders(self):
        mock_file = Mock(spec=ConfigFile)
        content: dict[str, Any] = {
            UserConfigs.SEARCH_FOLDERS: [
                {UserConfigs.SEARCH_PATH: "/test/search1"},
                {UserConfigs.SEARCH_PATH: "/test/search2"},
            ]
        }

        with patch("icon_manager.config.user.get_icons_search_folder") as mock_get_folder:
            mock_folder1 = Mock(spec=IconSearchFolder)
            mock_folder1.exists.return_value = True
            mock_folder2 = Mock(spec=IconSearchFolder)
            mock_folder2.exists.return_value = False
            mock_folder2.name = "search2"
            mock_folder2.path = "/test/search2"
            mock_get_folder.side_effect = [mock_folder1, mock_folder2]

            result = get_search_folders(mock_file, content)

            assert len(result) == 1
            assert result[0] == mock_folder1

    def test_get_search_folders_raises_error_when_missing(self):
        mock_file = Mock(spec=ConfigFile)
        mock_file.path = "/test/config.json"
        content = {}

        with pytest.raises(ValueError, match="Search folders DOES NOT exists in /test/config.json"):
            get_search_folders(mock_file, content)

    def test_get_search_folders_raises_error_when_empty_list(self):
        mock_file = Mock(spec=ConfigFile)
        mock_file.path = "/test/config.json"
        content: dict[str, Any] = {
            UserConfigs.SEARCH_FOLDERS: [],
        }

        with pytest.raises(ValueError, match="Search folders specified in /test/config.json"):
            get_search_folders(mock_file, content)

    def test_get_search_folders_raises_error_when_invalid_config(self):
        mock_file = Mock(spec=ConfigFile)
        content: dict[str, Any] = {
            UserConfigs.SEARCH_FOLDERS: ["invalid_config"],
        }

        with pytest.raises(ValueError, match="Search folder config is a list of Dicts"):
            get_search_folders(mock_file, content)


class TestUserConfigFactory:
    @pytest.fixture
    def mock_json_source(self):
        return Mock(spec=JsonSource)

    @pytest.fixture
    def factory(self, mock_json_source):
        return UserConfigFactory(mock_json_source)

    def test_init_creates_factory_with_source(self, mock_json_source):
        factory = UserConfigFactory(mock_json_source)
        assert factory.source == mock_json_source

    def test_create_builds_user_config_from_file(self, factory):
        mock_file = Mock(spec=ConfigFile)
        mock_file.name = "test_config"

        factory.source.read.return_value = {
            UserConfigs.CONFIG_SECTION: {
                UserConfigs.ICONS_PATH: "/test/icons",
                UserConfigs.SEARCH_FOLDERS: [
                    {
                        UserConfigs.SEARCH_PATH: "/test/search1",
                        UserConfigs.COPY_ICONS: True,
                    }
                ],
                UserConfigs.COPY_ICONS: True,
                UserConfigs.BEFORE_OR_AFTER: ["before", "after"],
                UserConfigs.CODE_FOLDERS: ["code1"],
                UserConfigs.EXCLUDE_FOLDERS: ["exclude1"],
            }
        }

        with patch("icon_manager.config.user.get_icons_path") as mock_get_icons:
            with patch("icon_manager.config.user.get_search_folders") as mock_get_search:
                mock_icons_path = Mock(spec=SearchFolder)
                mock_search_folders = [Mock(spec=IconSearchFolder)]
                mock_get_icons.return_value = mock_icons_path
                mock_get_search.return_value = mock_search_folders

                result = factory.create(mock_file)

                assert isinstance(result, UserConfig)
                assert result.name == "test_config"
                assert result.icons_path == mock_icons_path
                assert result.search_folders == mock_search_folders
                assert result.copy_icon is True
                assert result.before_or_after == {"before", "after"}
                assert result.code_folders == ["code1"]
                assert result.exclude_folders == ["exclude1"]

    def test_create_uses_defaults_for_missing_config(self, factory):
        mock_file = Mock(spec=ConfigFile)
        mock_file.name = "test_config"

        factory.source.read.return_value = {
            UserConfigs.CONFIG_SECTION: {
                UserConfigs.ICONS_PATH: "/test/icons",
                UserConfigs.SEARCH_FOLDERS: [],
            }
        }

        with patch("icon_manager.config.user.get_icons_path") as mock_get_icons:
            with patch("icon_manager.config.user.get_search_folders") as mock_get_search:
                mock_icons_path = Mock(spec=SearchFolder)
                mock_get_icons.return_value = mock_icons_path
                mock_get_search.return_value = []

                result = factory.create(mock_file)

                assert result.copy_icon is False
                assert result.before_or_after == set()
                assert result.code_folders == []
                assert result.exclude_folders == []

    def test_copy_user_config_template_copies_template(self, factory):
        mock_config = Mock(spec=ConfigFile)

        with patch("icon_manager.config.user.user_config_template_file") as mock_template:
            mock_template_file = Mock()
            mock_template.return_value = mock_template_file

            factory.copy_user_config_template(mock_config)

            mock_template_file.copy_to.assert_called_once_with(mock_config)

    def test_prepare_template_clears_template_values(self, factory):
        mock_config = Mock(spec=ConfigFile)

        factory.source.read.return_value = {
            UserConfigs.CONFIG_SECTION: {
                UserConfigs.SEARCH_FOLDERS: [{"path": "/test"}],
                UserConfigs.BEFORE_OR_AFTER: ["before"],
                UserConfigs.ICONS_PATH: "/test/icons",
                UserConfigs.COPY_ICONS: True,
                "other_config": "value",
            }
        }

        factory.prepare_template(mock_config)

        # Verify that write was called with cleared values
        write_call_args = factory.source.write.call_args[0][1]
        config_section = write_call_args[UserConfigs.CONFIG_SECTION]

        assert config_section[UserConfigs.SEARCH_FOLDERS] == []
        assert config_section[UserConfigs.BEFORE_OR_AFTER] == []
        assert config_section[UserConfigs.ICONS_PATH] == ""
        assert config_section[UserConfigs.COPY_ICONS] is False
        assert "other_config" in config_section

    def test_prepare_template_raises_error_when_content_none(self, factory):
        mock_config = Mock(spec=ConfigFile)
        factory.source.read.return_value = None

        with pytest.raises(RuntimeError, match="Should not be possible"):
            factory.prepare_template(mock_config)

    def test_create_template_combines_copy_and_prepare(self, factory):
        mock_config = Mock(spec=ConfigFile)

        with patch.object(factory, "copy_user_config_template") as mock_copy:
            with patch.object(factory, "prepare_template") as mock_prepare:
                result = factory.create_template(mock_config)

                mock_copy.assert_called_once_with(mock_config)
                mock_prepare.assert_called_once_with(mock_config)
                assert result == mock_config
