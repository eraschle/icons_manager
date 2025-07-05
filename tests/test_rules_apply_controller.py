from unittest.mock import Mock, patch

import pytest

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.rules_apply import (
    RulesApplyBuilder,
    RulesApplyController,
    RulesApplyOptions,
)
from icon_manager.content.models.matched import MatchedRuleFolder
from icon_manager.interfaces.path import Folder, FolderModel
from icon_manager.library.models import IconSetting, LibraryIconFile
from icon_manager.rules.manager import ExcludeManager


class TestRulesApplyBuilder:
    @pytest.fixture
    def builder(self):
        return RulesApplyBuilder()

    def test_init_creates_builder_with_empty_settings(self):
        builder = RulesApplyBuilder()
        assert list(builder.settings) == []

    def test_setup_configures_settings(self, builder):
        mock_settings = [Mock(spec=IconSetting), Mock(spec=IconSetting)]

        builder.setup(settings=mock_settings)

        assert builder.settings == mock_settings

    def test_setup_uses_empty_list_as_default(self, builder):
        builder.setup()

        assert list(builder.settings) == []

    def test_icon_setting_for_returns_matching_setting(self, builder):
        mock_folder = Mock(spec=Folder)
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.is_config_for.return_value = False
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.is_config_for.return_value = True

        builder.settings = [mock_setting1, mock_setting2]

        result = builder.icon_setting_for(mock_folder)

        assert result == mock_setting2
        mock_setting1.is_config_for.assert_called_once_with(mock_folder)
        mock_setting2.is_config_for.assert_called_once_with(mock_folder)

    def test_icon_setting_for_returns_none_when_no_match(self, builder):
        mock_folder = Mock(spec=Folder)
        mock_setting = Mock(spec=IconSetting)
        mock_setting.is_config_for.return_value = False

        builder.settings = [mock_setting]

        result = builder.icon_setting_for(mock_folder)

        assert result is None

    def test_get_matched_folder_creates_matched_folder_when_config_found(self, builder):
        mock_folder = Mock(spec=Folder)
        mock_folder.path = "/test/folder"
        mock_folder.name = "test_folder"

        mock_setting = Mock(spec=IconSetting)
        mock_setting.icon = Mock(spec=LibraryIconFile)
        mock_setting.icon.name_wo_extension = "test_icon"

        with patch.object(builder, "icon_setting_for") as mock_icon_setting:
            mock_icon_setting.return_value = mock_setting

            result = builder.get_matched_folder(mock_folder)

            assert isinstance(result, MatchedRuleFolder)
            assert isinstance(result.icon_folder, FolderModel)
            assert result.icon_folder.path == "/test/folder/__icon__"
            assert result.setting == mock_setting

    def test_get_matched_folder_returns_none_when_no_config(self, builder):
        mock_folder = Mock(spec=Folder)

        with patch.object(builder, "icon_setting_for") as mock_icon_setting:
            mock_icon_setting.return_value = None

            result = builder.get_matched_folder(mock_folder)

            assert result is None

    def test_can_build_folder_always_returns_true(self, builder):
        mock_folder = Mock(spec=Folder)

        result = builder.can_build_folder(mock_folder)

        assert result is True

    def test_build_folder_model_delegates_to_get_matched_folder(self, builder):
        mock_folder = Mock(spec=Folder)
        mock_matched_folder = Mock(spec=MatchedRuleFolder)

        with patch.object(builder, "get_matched_folder") as mock_get_matched:
            mock_get_matched.return_value = mock_matched_folder

            result = builder.build_folder_model(mock_folder)

            mock_get_matched.assert_called_once_with(mock_folder)
            assert result == mock_matched_folder


class TestRulesApplyOptions:
    @pytest.fixture
    def mock_exclude_manager(self):
        return Mock(spec=ExcludeManager)

    @pytest.fixture
    def options(self, mock_exclude_manager):
        return RulesApplyOptions(mock_exclude_manager)

    def test_init_creates_options_with_exclude_manager(self, mock_exclude_manager):
        options = RulesApplyOptions(mock_exclude_manager)

        assert options.exclude == mock_exclude_manager
        assert options.clean_excluded is True
        assert options.clean_project is True
        assert options.clean_recursive is True

    def test_no_filter_options_returns_true_when_all_disabled_and_exclude_empty(self, options):
        options.clean_excluded = False
        options.clean_project = False
        options.clean_recursive = False
        options.exclude.is_empty.return_value = True

        result = options.no_filter_options()

        assert result is True

    def test_no_filter_options_returns_false_when_any_filter_enabled(self, options):
        options.clean_excluded = True
        options.clean_project = False
        options.clean_recursive = False
        options.exclude.is_empty.return_value = True

        result = options.no_filter_options()

        assert result is False

    def test_no_filter_options_returns_false_when_exclude_not_empty(self, options):
        options.clean_excluded = False
        options.clean_project = False
        options.clean_recursive = False
        options.exclude.is_empty.return_value = False

        result = options.no_filter_options()

        assert result is False


class TestRulesApplyController:
    @pytest.fixture
    def mock_user_config(self):
        user_config = Mock(spec=UserConfig)
        user_config.name = "TestUserConfig"
        return user_config

    @pytest.fixture
    def mock_builder(self):
        return Mock(spec=RulesApplyBuilder)

    @pytest.fixture
    def controller(self, mock_user_config, mock_builder):
        return RulesApplyController(mock_user_config, mock_builder)

    def test_init_creates_controller_with_dependencies(self, mock_user_config, mock_builder):
        controller = RulesApplyController(mock_user_config, mock_builder)

        assert controller.user_config == mock_user_config
        assert controller.builder == mock_builder
        assert controller.folders == []

    def test_init_uses_default_builder_when_not_provided(self, mock_user_config):
        controller = RulesApplyController(mock_user_config)

        assert isinstance(controller.builder, RulesApplyBuilder)

    @patch("icon_manager.content.controller.rules_apply.filter_folders")
    def test_crawle_and_build_result_filters_folders(self, mock_filter_folders, controller):
        mock_folders = [Mock(spec=Folder), Mock(spec=Folder)]
        mock_exclude = Mock(spec=ExcludeManager)
        mock_filtered_folders = [Mock(spec=Folder)]

        mock_filter_folders.return_value = mock_filtered_folders

        result = controller.crawle_and_build_result(mock_folders, mock_exclude)

        mock_filter_folders.assert_called_once()
        filter_call_args = mock_filter_folders.call_args[0]
        assert filter_call_args[0] == mock_folders
        assert isinstance(filter_call_args[1], RulesApplyOptions)
        assert filter_call_args[1].exclude == mock_exclude
        assert result == mock_filtered_folders

    def test_search_and_find_matches_configures_builder_and_builds_models(self, controller):
        mock_folders = [Mock(spec=Folder), Mock(spec=Folder)]
        mock_settings = [Mock(spec=IconSetting)]
        mock_matched_folders = [Mock(spec=MatchedRuleFolder)]

        controller.builder.build_models.return_value = mock_matched_folders

        controller.search_and_find_matches(mock_folders, mock_settings)

        controller.builder.setup.assert_called_once_with(settings=mock_settings)
        controller.builder.build_models.assert_called_once_with(mock_folders)
        assert controller.folders == mock_matched_folders

    @patch("icon_manager.content.controller.rules_apply.CreateIconAction")
    def test_creating_found_matches_executes_create_action(self, mock_action_class, controller):
        mock_matched_folders = [Mock(spec=MatchedRuleFolder)]
        controller.folders = mock_matched_folders
        mock_exclude = Mock(spec=ExcludeManager)

        mock_action = Mock()
        mock_action.any_executed.return_value = True
        mock_action.get_log_message.return_value = "Created icons"
        mock_action_class.return_value = mock_action

        controller.creating_found_matches(mock_exclude)

        mock_action_class.assert_called_once_with(mock_matched_folders, controller.user_config)
        mock_action.execute.assert_called_once()
        mock_action.get_log_message.assert_called_once_with(MatchedRuleFolder)

    @patch("icon_manager.content.controller.rules_apply.CreateIconAction")
    def test_creating_found_matches_skips_logging_when_nothing_executed(self, mock_action_class, controller):
        controller.folders = []
        mock_exclude = Mock(spec=ExcludeManager)

        mock_action = Mock()
        mock_action.any_executed.return_value = False
        mock_action_class.return_value = mock_action

        controller.creating_found_matches(mock_exclude)

        mock_action.execute.assert_called_once()
        mock_action.get_log_message.assert_not_called()

    @patch("icon_manager.content.controller.rules_apply.ReCreateIconAction")
    def test_re_apply_matches_executes_recreate_action(self, mock_action_class, controller):
        mock_re_apply_controller = Mock()

        mock_action = Mock()
        mock_action.any_executed.return_value = True
        mock_action.get_log_message.return_value = "Re-applied icons"
        mock_action_class.return_value = mock_action

        controller.re_apply_matches(mock_re_apply_controller)

        mock_action_class.assert_called_once_with(mock_re_apply_controller, controller.user_config)
        mock_action.execute.assert_called_once()
        mock_action.get_log_message.assert_called_once_with(MatchedRuleFolder)

    @patch("icon_manager.content.controller.rules_apply.ReCreateIconAction")
    def test_re_apply_matches_skips_logging_when_nothing_executed(self, mock_action_class, controller):
        mock_re_apply_controller = Mock()

        mock_action = Mock()
        mock_action.any_executed.return_value = False
        mock_action_class.return_value = mock_action

        controller.re_apply_matches(mock_re_apply_controller)

        mock_action.execute.assert_called_once()
        mock_action.get_log_message.assert_not_called()

    def test_delete_content_is_empty_implementation(self, controller):
        # This test verifies that delete_content exists and doesn't raise an error
        # The current implementation is empty (pass statement)
        controller.delete_content()
        # If we reach here, the method executed without error

    def test_integration_workflow(self, controller):
        # Test the typical workflow integration
        mock_folders = [Mock(spec=Folder)]
        mock_settings = [Mock(spec=IconSetting)]
        mock_exclude = Mock(spec=ExcludeManager)
        mock_matched_folders = [Mock(spec=MatchedRuleFolder)]

        # Setup mocks
        with patch("icon_manager.content.controller.rules_apply.filter_folders") as mock_filter:
            mock_filter.return_value = mock_folders
            controller.builder.build_models.return_value = mock_matched_folders

            with patch("icon_manager.content.controller.rules_apply.CreateIconAction") as mock_action_class:
                mock_action = Mock()
                mock_action.any_executed.return_value = True
                mock_action.get_log_message.return_value = "Success"
                mock_action_class.return_value = mock_action

                # Execute workflow
                filtered_folders = controller.crawle_and_build_result(mock_folders, mock_exclude)
                controller.search_and_find_matches(filtered_folders, mock_settings)
                controller.creating_found_matches(mock_exclude)

                # Verify workflow
                assert controller.folders == mock_matched_folders
                controller.builder.setup.assert_called_once_with(settings=mock_settings)
                mock_action.execute.assert_called_once()
