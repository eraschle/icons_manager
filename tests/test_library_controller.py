from unittest.mock import Mock, patch

import pytest

from icon_manager.content.models.matched import IconSetting
from icon_manager.interfaces.path import File, FileModel, JsonFile
from icon_manager.library.controller import (
    IconLibraryController,
    IconSettingBuilder,
    LibraryIconFileBuilder,
    RuleManagerBuilder,
)
from icon_manager.library.models import ArchiveFolder, IconFile, LibraryIconFile
from icon_manager.rules.factory.manager import RuleManagerFactory
from icon_manager.rules.manager import RuleManager


class TestRuleManagerBuilder:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=RuleManagerFactory)

    @pytest.fixture
    def builder(self, mock_factory):
        return RuleManagerBuilder(mock_factory)

    def test_init_creates_builder_with_factory(self, mock_factory):
        builder = RuleManagerBuilder(mock_factory)
        assert builder.factory == mock_factory

    def test_init_uses_default_factory_when_not_provided(self):
        builder = RuleManagerBuilder()
        assert isinstance(builder.factory, RuleManagerFactory)

    def test_can_build_file_returns_true_for_json_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/config.json"

        with patch.object(JsonFile, "is_model") as mock_is_model:
            mock_is_model.return_value = True

            result = builder.can_build_file(mock_file)

            assert result is True
            mock_is_model.assert_called_once_with("/test/config.json")

    def test_can_build_file_returns_false_for_non_json_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/file.txt"

        with patch.object(JsonFile, "is_model") as mock_is_model:
            mock_is_model.return_value = False

            result = builder.can_build_file(mock_file)

            assert result is False

    def test_build_file_model_creates_rule_manager(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/config.json"
        mock_rule_manager = Mock(spec=RuleManager)

        builder.factory.create.return_value = mock_rule_manager

        result = builder.build_file_model(mock_file)

        builder.factory.create.assert_called_once()
        created_json_file = builder.factory.create.call_args[0][0]
        assert isinstance(created_json_file, JsonFile)
        assert created_json_file.path == "/test/config.json"
        assert result == mock_rule_manager


class TestLibraryIconFileBuilder:
    @pytest.fixture
    def builder(self):
        return LibraryIconFileBuilder()

    def test_can_build_file_returns_true_for_icon_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.name = "icon.ico"

        with patch.object(LibraryIconFile, "is_model") as mock_is_model:
            mock_is_model.return_value = True

            result = builder.can_build_file(mock_file)

            assert result is True
            mock_is_model.assert_called_once_with("icon.ico")

    def test_can_build_file_returns_false_for_non_icon_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.name = "document.txt"

        with patch.object(LibraryIconFile, "is_model") as mock_is_model:
            mock_is_model.return_value = False

            result = builder.can_build_file(mock_file)

            assert result is False

    def test_build_file_model_creates_library_icon_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/icon.ico"

        result = builder.build_file_model(mock_file)

        assert isinstance(result, LibraryIconFile)
        assert result.path == "/test/icon.ico"


class TestIconSettingBuilder:
    @pytest.fixture
    def mock_icon_builder(self):
        return Mock(spec=LibraryIconFileBuilder)

    @pytest.fixture
    def mock_config_builder(self):
        return Mock(spec=RuleManagerBuilder)

    @pytest.fixture
    def builder(self, mock_icon_builder, mock_config_builder):
        return IconSettingBuilder(mock_icon_builder, mock_config_builder)

    def test_init_creates_builder_with_dependencies(self, mock_icon_builder, mock_config_builder):
        builder = IconSettingBuilder(mock_icon_builder, mock_config_builder)

        assert builder.icon_builder == mock_icon_builder
        assert builder.config_builder == mock_config_builder
        assert builder.rule_configs == {}

    def test_init_uses_default_builders_when_not_provided(self):
        builder = IconSettingBuilder()

        assert isinstance(builder.icon_builder, LibraryIconFileBuilder)
        assert isinstance(builder.config_builder, RuleManagerBuilder)

    def test_update_rules_builds_and_stores_rule_configs(self, builder):
        mock_files = [Mock(spec=File), Mock(spec=File)]
        mock_rule1 = Mock(spec=RuleManager)
        mock_rule1.name = "rule1"
        mock_rule2 = Mock(spec=RuleManager)
        mock_rule2.name = "rule2"

        builder.config_builder.build_models.return_value = [mock_rule1, mock_rule2]

        builder.update_rules(mock_files)

        builder.config_builder.build_models.assert_called_once_with(mock_files)
        assert builder.rule_configs == {"rule1": mock_rule1, "rule2": mock_rule2}

    def test_build_icons_delegates_to_icon_builder(self, builder):
        mock_files = [Mock(spec=File)]
        mock_icons = [Mock(spec=LibraryIconFile)]

        builder.icon_builder.build_models.return_value = mock_icons

        result = builder.build_icons(mock_files)

        builder.icon_builder.build_models.assert_called_once_with(mock_files)
        assert result == mock_icons

    def test_get_rule_manager_returns_matching_manager(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)
        mock_icon.name_wo_extension = "test_icon"
        mock_rule = Mock(spec=RuleManager)

        builder.rule_configs = {"test_icon": mock_rule}

        result = builder.get_rule_manager(mock_icon)

        assert result == mock_rule

    def test_get_rule_manager_returns_none_when_no_match(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)
        mock_icon.name_wo_extension = "unknown_icon"

        builder.rule_configs = {"test_icon": Mock()}

        result = builder.get_rule_manager(mock_icon)

        assert result is None

    def test_can_build_returns_true_for_library_icon_with_config(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)
        mock_rule = Mock(spec=RuleManager)

        with patch.object(builder, "get_rule_manager") as mock_get_rule:
            mock_get_rule.return_value = mock_rule

            result = builder.can_build(mock_icon)

            assert result is True

    def test_can_build_returns_false_for_non_library_icon(self, builder):
        mock_file = Mock(spec=File)

        result = builder.can_build(mock_file)

        assert result is False

    def test_can_build_returns_false_for_library_icon_without_config(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)

        with patch.object(builder, "get_rule_manager") as mock_get_rule:
            mock_get_rule.return_value = None

            result = builder.can_build(mock_icon)

            assert result is False

    def test_build_model_creates_icon_setting(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)
        mock_rule = Mock(spec=RuleManager)

        with patch.object(builder, "get_rule_manager") as mock_get_rule:
            mock_get_rule.return_value = mock_rule

            result = builder.build_model(mock_icon)

            assert isinstance(result, IconSetting)
            assert result.icon == mock_icon
            assert result.manager == mock_rule

    def test_build_model_returns_none_when_no_config(self, builder):
        mock_icon = Mock(spec=LibraryIconFile)

        with patch.object(builder, "get_rule_manager") as mock_get_rule:
            mock_get_rule.return_value = None

            result = builder.build_model(mock_icon)

            assert result is None

    def test_update_config_delegates_to_factory(self, builder):
        mock_setting = Mock(spec=IconSetting)
        mock_setting.manager = Mock(spec=RuleManager)
        mock_config = Mock(spec=JsonFile)
        mock_setting.manager.config = mock_config
        mock_template = Mock(spec=JsonFile)

        builder.config_builder.factory = Mock()

        builder.update_config(mock_setting, mock_template)

        builder.config_builder.factory.update.assert_called_once_with(mock_config, mock_template)


class TestIconLibraryController:
    @pytest.fixture
    def mock_builder(self):
        return Mock(spec=IconSettingBuilder)

    @pytest.fixture
    def controller(self, mock_builder):
        controller = IconLibraryController(mock_builder)
        return controller

    def test_init_creates_controller_with_builder(self, mock_builder):
        controller = IconLibraryController(mock_builder)

        assert controller.builder == mock_builder
        assert list(controller.library_icons) == []
        assert controller._settings == []

    def test_init_uses_default_builder_when_not_provided(self):
        controller = IconLibraryController()

        assert isinstance(controller.builder, IconSettingBuilder)

    def test_icons_extensions_contains_expected_extensions(self):
        extensions = IconLibraryController.icons_extensions

        assert "ico" in extensions
        assert "json" in extensions

    def test_settings_returns_all_settings_when_clean_empty_false(self, controller):
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.is_empty.return_value = True
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.is_empty.return_value = False

        controller._settings = [mock_setting1, mock_setting2]

        result = controller.settings(clean_empty=False)

        assert result == [mock_setting1, mock_setting2]

    def test_settings_filters_empty_settings_when_clean_empty_true(self, controller):
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.is_empty.return_value = True
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.is_empty.return_value = False

        controller._settings = [mock_setting1, mock_setting2]

        result = controller.settings(clean_empty=True)

        assert result == [mock_setting2]

    def test_create_icon_settings_configures_settings_with_before_or_after(self, controller):
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.is_empty.return_value = False
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.is_empty.return_value = False

        controller._settings = [mock_setting1, mock_setting2]
        before_or_after = ["before", "after"]

        result = controller.create_icon_settings(before_or_after)

        mock_setting1.set_before_or_after.assert_called_once_with(before_or_after)
        mock_setting2.set_before_or_after.assert_called_once_with(before_or_after)
        assert len(result) == 2

    def test_create_settings_builds_complete_settings(self, controller):
        mock_rules = [Mock(spec=File)]
        mock_icons = [Mock(spec=File)]
        mock_library_icons = [Mock(spec=LibraryIconFile)]
        icon_setting_template = Mock(spec=IconSetting)
        icon_setting_template.manager = Mock(spec=RuleManager)
        mock_settings = [icon_setting_template]

        content = {"json": mock_rules, "ico": mock_icons}

        controller.builder.build_icons.return_value = mock_library_icons
        controller.builder.build_models.return_value = mock_settings

        for setting in mock_settings:
            setting.manager.clean_empty = Mock()
            setting.order_key = 1

        controller.create_settings(content)

        controller.builder.update_rules.assert_called_once_with(rules=mock_rules)
        controller.builder.build_icons.assert_called_once_with(mock_icons)
        controller.builder.build_models.assert_called_once_with(mock_library_icons)
        assert controller.library_icons == mock_library_icons
        assert controller._settings == mock_settings

    def test_clean_empty_rules_calls_clean_empty_on_all_settings(self, controller):
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.manager = Mock(spec=RuleManager)
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.manager = Mock(spec=RuleManager)
        controller._settings = [mock_setting1, mock_setting2]

        controller.clean_empty_rules()

        mock_setting1.manager.clean_empty.assert_called_once()
        mock_setting2.manager.clean_empty.assert_called_once()

    @patch("icon_manager.library.controller.icon_setting_template")
    def test_create_icon_configs_creates_templates_for_missing_configs(self, mock_template_func, controller):
        mock_template = Mock()
        mock_template_func.return_value = mock_template

        mock_icon1 = Mock(spec=LibraryIconFile)
        mock_config1 = Mock()
        mock_config1.exists.return_value = False
        mock_icon1.get_config.return_value = mock_config1
        mock_icon1.name_wo_extension = "icon1"

        mock_icon2 = Mock(spec=LibraryIconFile)
        mock_config2 = Mock()
        mock_config2.exists.return_value = True
        mock_icon2.get_config.return_value = mock_config2

        controller.library_icons = [mock_icon1, mock_icon2]

        controller.create_icon_configs()

        mock_template.copy_to.assert_called_once_with(mock_config1)
        assert mock_template.copy_to.call_count == 1

    @patch("icon_manager.library.controller.icon_setting_template")
    def test_update_icon_configs_updates_all_settings(self, mock_template_func, controller):
        mock_template = Mock()
        mock_template_func.return_value = mock_template

        mock_setting1 = Mock(spec=IconSetting)
        mock_setting2 = Mock(spec=IconSetting)
        controller._settings = [mock_setting1, mock_setting2]

        controller.update_icon_configs()

        controller.builder.update_config.assert_any_call(mock_setting1, mock_template)
        controller.builder.update_config.assert_any_call(mock_setting2, mock_template)

    @patch("icon_manager.library.controller.DeleteAction")
    def test_delete_icon_configs_executes_delete_action(self, mock_action_class, controller):
        mock_setting1 = Mock(spec=IconSetting)
        manager1 = Mock(spec=RuleManager)
        manager1.config = Mock(spec=JsonFile)
        mock_setting1.manager = manager1

        manager2 = Mock(spec=RuleManager)
        manager2.config = Mock(spec=JsonFile)
        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.manager = manager2
        controller._settings = [mock_setting1, mock_setting2]

        mock_action = Mock()
        mock_action.any_executed.return_value = True
        mock_action.get_log_message.return_value = "Deleted configs"
        mock_action_class.return_value = mock_action

        controller.delete_icon_configs()

        expected_configs = [mock_setting1.manager.config, mock_setting2.manager.config]
        mock_action_class.assert_called_once_with(expected_configs)
        mock_action.execute.assert_called_once()

    def test_archive_library_archives_empty_settings(self, controller):
        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.is_empty.return_value = True
        mock_setting1.archive_files.return_value = [Mock(spec=FileModel)]
        mock_setting1.name = "setting1"

        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.is_empty.return_value = False

        controller._settings = [mock_setting1, mock_setting2]

        with patch.object(controller, "archive_file") as mock_archive_file:
            controller.archive_library()

            mock_archive_file.assert_called_once()
            mock_setting2.archive_files.assert_not_called()

    def test_archive_file_copies_and_removes_file(self, controller):
        mock_file = Mock(spec=FileModel)
        mock_folder = Mock(spec=ArchiveFolder)
        mock_archive = Mock()
        mock_folder.get_archive_file.return_value = mock_archive

        with patch.object(controller, "get_archive_folder") as mock_get_folder:
            mock_get_folder.return_value = mock_folder

            controller.archive_file(mock_file)

            mock_file.copy_to.assert_called_once_with(mock_archive)
            mock_file.remove.assert_called_once()

    def test_get_archive_folder_creates_folder_if_not_exists(self, controller):
        mock_icon = Mock(spec=FileModel)

        with patch.object(ArchiveFolder, "get_folder_path") as mock_get_path:
            mock_get_path.return_value = "/test/archive"

            with patch.object(ArchiveFolder, "__new__") as mock_archive_new:
                mock_folder = Mock(spec=ArchiveFolder)
                mock_folder.exists.return_value = False
                mock_archive_new.return_value = mock_folder

                result = controller.get_archive_folder(mock_icon)

                mock_folder.create.assert_called_once()
                assert result == mock_folder

    def test_setting_by_icon_returns_matching_setting(self, controller):
        mock_icon = Mock(spec=IconFile)
        mock_icon.name = "test_icon.ico"

        mock_setting1 = Mock(spec=IconSetting)
        mock_setting1.icon = Mock(spec=IconFile)
        mock_setting1.icon.name = "other_icon.ico"

        mock_setting2 = Mock(spec=IconSetting)
        mock_setting2.icon = Mock(spec=IconFile)
        mock_setting2.icon.name = "test_icon.ico"

        controller._settings = [mock_setting1, mock_setting2]

        result = controller.setting_by_icon(mock_icon)

        assert result == mock_setting2

    def test_setting_by_icon_returns_none_when_no_match(self, controller):
        mock_icon = Mock(spec=IconFile)
        mock_icon.name = "unknown_icon.ico"

        mock_setting = Mock(spec=IconSetting)
        mock_setting.icon = Mock(spec=IconFile)
        mock_setting.icon.name = "test_icon.ico"

        controller._settings = [mock_setting]

        result = controller.setting_by_icon(mock_icon)

        assert result is None
