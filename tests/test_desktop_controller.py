from unittest.mock import Mock, patch

import pytest

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import (
    DesktopDeleteAction,
    DesktopFileChecker,
    DesktopIniBuilder,
    DesktopIniCommand,
    DesktopIniController,
    DesktopIniCreator,
    IconFileCommand,
    IconFolderCommand,
    RuleFolderCommand,
    error_message,
    get_commands,
)
from icon_manager.content.models.desktop import DesktopIniFile, Git
from icon_manager.content.models.matched import (
    MatchedIconFile,
    MatchedIconFolder,
    MatchedRuleFolder,
)
from icon_manager.data.ini_source import DesktopFileSource
from icon_manager.interfaces.path import File, Folder, PathModel
from icon_manager.library.models import IconSetting, LibraryIconFile


class TestDesktopFileChecker:
    @pytest.fixture
    def mock_source(self):
        return Mock(spec=DesktopFileSource)

    @pytest.fixture
    def checker(self, mock_source):
        return DesktopFileChecker(mock_source)

    def test_init_creates_checker_with_source(self, mock_source):
        checker = DesktopFileChecker(mock_source)
        assert checker.source == mock_source

    def test_is_app_file_returns_true_when_app_entry_found(self, checker, mock_source):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/desktop.ini"

        mock_source.read.return_value = [
            "[.ShellClassInfo]",
            "IconResource=icon.ico,0",
            "IconManager=1",
            "[ViewState]",
        ]

        result = checker.is_app_file(mock_file)

        assert result is True

    def test_is_app_file_returns_false_when_app_entry_not_found(self, checker, mock_source):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/desktop.ini"

        mock_source.read.return_value = [
            "[.ShellClassInfo]",
            "IconResource=icon.ico,0",
            "[ViewState]",
        ]

        result = checker.is_app_file(mock_file)

        assert result is False

    def test_is_app_file_handles_desktop_ini_file_input(self, checker, mock_source):
        mock_desktop_file = Mock(spec=DesktopIniFile)

        mock_source.read.return_value = ["IconManager=1"]

        result = checker.is_app_file(mock_desktop_file)

        assert result is True
        mock_source.read.assert_called_once_with(mock_desktop_file)


class TestDesktopIniBuilder:
    @pytest.fixture
    def mock_source(self):
        return Mock(spec=DesktopFileSource)

    @pytest.fixture
    def builder(self, mock_source):
        return DesktopIniBuilder(mock_source)

    def test_init_creates_builder_with_checker(self, mock_source):
        builder = DesktopIniBuilder(mock_source)
        assert isinstance(builder.checker, DesktopFileChecker)
        assert builder.checker.source == mock_source

    def test_app_entry_constant(self):
        assert DesktopIniBuilder.app_entry == "IconManager=1"

    def test_can_build_file_returns_true_for_valid_desktop_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/desktop.ini"

        with patch.object(DesktopIniFile, "is_model") as mock_is_model:
            mock_is_model.return_value = True
            builder.checker.is_app_file = Mock(return_value=True)

            result = builder.can_build_file(mock_file)

            assert result is True
            mock_is_model.assert_called_once_with("/test/desktop.ini")
            builder.checker.is_app_file.assert_called_once_with(mock_file)

    def test_can_build_file_returns_false_for_invalid_desktop_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/desktop.ini"

        with patch.object(DesktopIniFile, "is_model") as mock_is_model:
            mock_is_model.return_value = True
            builder.checker.is_app_file = Mock(return_value=False)

            result = builder.can_build_file(mock_file)

            assert result is False

    def test_build_file_model_creates_desktop_ini_file(self, builder):
        mock_file = Mock(spec=File)
        mock_file.path = "/test/desktop.ini"

        result = builder.build_file_model(mock_file)

        assert isinstance(result, DesktopIniFile)
        assert result.path == "/test/desktop.ini"


class TestDesktopDeleteAction:
    @pytest.fixture
    def mock_checker(self):
        return Mock(spec=DesktopFileChecker)

    @pytest.fixture
    def delete_action(self, mock_checker):
        mock_entries = [Mock(spec=PathModel), Mock(spec=PathModel)]
        return DesktopDeleteAction(mock_entries, mock_checker)

    def test_init_creates_action_with_entries_and_checker(self, mock_checker):
        mock_entries = [Mock(spec=PathModel)]
        action = DesktopDeleteAction(mock_entries, mock_checker)

        assert action.entries == mock_entries
        assert action.checker == mock_checker

    def test_can_execute_returns_true_when_app_file_and_exists(self, delete_action, mock_checker):
        mock_entry = Mock(spec=PathModel)
        mock_entry.exists.return_value = True
        mock_checker.is_app_file.return_value = True

        result = delete_action.can_execute(mock_entry)

        assert result is True
        mock_checker.is_app_file.assert_called_once_with(mock_entry)

    def test_can_execute_returns_false_when_not_app_file(self, delete_action, mock_checker):
        mock_entry = Mock(spec=PathModel)
        mock_entry.exists.return_value = True
        mock_checker.is_app_file.return_value = False

        result = delete_action.can_execute(mock_entry)

        assert result is False


class TestDesktopIniController:
    @pytest.fixture
    def mock_user_config(self):
        user_config = Mock(spec=UserConfig)
        user_config.name = "TestConfig"
        return user_config

    @pytest.fixture
    def mock_builder(self):
        return Mock(spec=DesktopIniBuilder)

    @pytest.fixture
    def controller(self, mock_user_config, mock_builder):
        return DesktopIniController(mock_user_config, mock_builder)

    def test_init_creates_controller_with_dependencies(self, mock_user_config, mock_builder):
        controller = DesktopIniController(mock_user_config, mock_builder)

        assert controller.user_config == mock_user_config
        assert controller.builder == mock_builder
        assert controller.desktop_files == []

    @patch("icon_manager.content.controller.desktop.files_by_extension")
    def test_crawle_and_build_result_builds_desktop_files(self, mock_files_by_ext, controller):
        mock_folders = [Mock(spec=Folder), Mock(spec=Folder)]
        mock_settings = [Mock(spec=IconSetting)]
        mock_files = [Mock(spec=File), Mock(spec=File)]
        mock_desktop_files = [Mock(spec=DesktopIniFile), Mock(spec=DesktopIniFile)]

        mock_files_by_ext.return_value = mock_files
        controller.builder.build_models.return_value = mock_desktop_files

        controller.crawle_and_build_result(mock_folders, mock_settings)

        mock_files_by_ext.assert_called_once_with(mock_folders, ["ini"])
        controller.builder.build_models.assert_called_once_with(mock_files)
        assert controller.desktop_files == mock_desktop_files

    @patch("icon_manager.content.controller.desktop.DesktopDeleteAction")
    @patch("icon_manager.content.controller.desktop.DesktopFileChecker")
    def test_delete_content_executes_delete_action(self, mock_checker_class, mock_action_class, controller):
        mock_desktop_files = [Mock(spec=DesktopIniFile)]
        controller.desktop_files = mock_desktop_files

        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker
        mock_action = Mock()
        mock_action.any_executed.return_value = True
        mock_action.get_log_message.return_value = "Deleted files"
        mock_action_class.return_value = mock_action

        controller.delete_content()

        mock_action_class.assert_called_once_with(mock_desktop_files, mock_checker)
        mock_action.execute.assert_called_once()
        mock_action.get_log_message.assert_called_once_with(DesktopIniFile)


class TestConfigCommands:
    def test_error_message_formats_correctly(self):
        mock_model = Mock(spec=PathModel)
        mock_model.name = "test_folder"

        result = error_message(mock_model, "test error")

        assert result == 'test_folder >> "test error"'

    def test_rule_folder_command_init(self):
        mock_rule_folder = Mock(spec=MatchedRuleFolder)
        command = RuleFolderCommand(1, True, mock_rule_folder)

        assert command.order == 1
        assert command.copy_icon is True
        assert command.rule_folder == mock_rule_folder

    def test_rule_folder_command_can_change_attribute(self):
        mock_rule_folder = Mock(spec=MatchedRuleFolder)
        mock_rule_folder.path = "/test/folder"
        mock_rule_folder.icon_folder.exists.return_value = True

        with patch.object(Git, "is_model") as mock_git_check:
            mock_git_check.return_value = False

            command = RuleFolderCommand(1, True, mock_rule_folder)
            result = command.can_change_attribute()

            assert result is True

    def test_rule_folder_command_pre_command_creates_icon_folder(self):
        mock_rule_folder = Mock(spec=MatchedRuleFolder)
        mock_rule_folder.path = "/test/folder"
        mock_rule_folder.icon_folder.exists.return_value = True

        with patch.object(Git, "is_model") as mock_git_check:
            mock_git_check.return_value = False

            command = RuleFolderCommand(1, True, mock_rule_folder)
            command.pre_command()

            mock_rule_folder.icon_folder.create.assert_called_once()

    def test_rule_folder_command_post_command_sets_read_only(self):
        mock_rule_folder = Mock(spec=MatchedRuleFolder)
        mock_rule_folder.path = "/test/folder"
        mock_rule_folder.icon_folder.exists.return_value = True

        with patch.object(Git, "is_model") as mock_git_check:
            mock_git_check.return_value = False

            command = RuleFolderCommand(1, True, mock_rule_folder)
            command.post_command()

            mock_rule_folder.set_read_only.assert_called_once_with(is_read_only=True)

    def test_icon_folder_command_pre_command_creates_folder_when_needed(self):
        mock_icon_folder = Mock(spec=MatchedIconFolder)
        mock_icon_folder.exists.return_value = False

        command = IconFolderCommand(2, True, mock_icon_folder)
        command.pre_command()

        mock_icon_folder.create.assert_called_once()

    def test_icon_folder_command_post_command_sets_hidden(self):
        mock_icon_folder = Mock(spec=MatchedIconFolder)
        mock_icon_folder.exists.return_value = True

        command = IconFolderCommand(2, True, mock_icon_folder)
        command.post_command()

        mock_icon_folder.set_hidden.assert_called_once_with(is_hidden=True)

    def test_icon_file_command_pre_command_copies_library_icon(self):
        mock_icon = Mock(spec=MatchedIconFile)
        mock_icon.exists.return_value = False
        mock_library = Mock(spec=LibraryIconFile)

        command = IconFileCommand(3, True, mock_icon, mock_library)
        command.pre_command()

        mock_library.copy_to.assert_called_once_with(mock_icon)

    def test_icon_file_command_post_command_sets_hidden(self):
        mock_icon = Mock(spec=MatchedIconFile)
        mock_icon.exists.return_value = True
        mock_library = Mock(spec=LibraryIconFile)

        command = IconFileCommand(3, True, mock_icon, mock_library)
        command.post_command()

        mock_icon.set_hidden.assert_called_once_with(is_hidden=True)

    def test_desktop_ini_command_pre_command_sets_writeable(self):
        mock_desktop = Mock(spec=DesktopIniFile)
        mock_desktop.exists.return_value = True

        command = DesktopIniCommand(4, True, mock_desktop)
        command.pre_command()

        mock_desktop.set_writeable_and_visible.assert_called_once()

    def test_desktop_ini_command_post_command_sets_protected(self):
        mock_desktop = Mock(spec=DesktopIniFile)
        mock_desktop.exists.return_value = True

        command = DesktopIniCommand(4, True, mock_desktop)
        command.post_command()

        mock_desktop.set_protected_and_hidden.assert_called_once()

    def test_get_commands_returns_ordered_commands(self):
        mock_rule_folder = Mock(spec=MatchedRuleFolder)
        mock_rule_folder.icon_folder = Mock(spec=MatchedIconFolder)
        mock_rule_folder.local_icon = Mock(spec=MatchedIconFile)
        mock_rule_folder.library_icon = Mock(spec=LibraryIconFile)
        mock_rule_folder.desktop_ini = Mock(spec=DesktopIniFile)

        commands = get_commands(mock_rule_folder, True)

        assert len(commands) == 4
        assert isinstance(commands[0], RuleFolderCommand)
        assert isinstance(commands[1], IconFolderCommand)
        assert isinstance(commands[2], IconFileCommand)
        assert isinstance(commands[3], DesktopIniCommand)
        assert all(cmd.order == i + 1 for i, cmd in enumerate(commands))


class TestDesktopIniCreator:
    @pytest.fixture
    def mock_source(self):
        return Mock(spec=DesktopFileSource)

    @pytest.fixture
    def creator(self, mock_source):
        return DesktopIniCreator(mock_source)

    def test_init_creates_creator_with_source_and_checker(self, mock_source):
        creator = DesktopIniCreator(mock_source)

        assert creator.source == mock_source
        assert isinstance(creator.checker, DesktopFileChecker)
        assert creator.commands == []

    def test_can_write_returns_true_for_non_existing_file(self, creator):
        mock_file = Mock(spec=DesktopIniFile)
        mock_file.exists.return_value = False

        result = creator.can_write(mock_file)

        assert result is True

    def test_can_write_returns_true_for_app_managed_file(self, creator):
        mock_file = Mock(spec=DesktopIniFile)
        mock_file.exists.return_value = True
        creator.checker.is_app_file = Mock(return_value=True)

        result = creator.can_write(mock_file)

        assert result is True

    def test_can_write_returns_false_for_existing_non_app_file(self, creator):
        mock_file = Mock(spec=DesktopIniFile)
        mock_file.exists.return_value = True
        creator.checker.is_app_file = Mock(return_value=False)

        result = creator.can_write(mock_file)

        assert result is False

    def test_create_content_generates_desktop_ini_content(self, creator):
        mock_manager = Mock(spec=MatchedRuleFolder)
        mock_manager.icon_path_for_desktop_ini.return_value = "icon.ico"

        result = list(creator.create_content(mock_manager))

        expected = [
            "[.ShellClassInfo]",
            "IconResource=icon.ico,0",
            "IconManager=1",
            "[ViewState]",
            "Mode=",
            "Vid=",
            "FolderType=Generic",
        ]
        assert result == expected

    def test_order_commands_sorts_by_order(self, creator):
        mock_cmd1 = Mock()
        mock_cmd1.order = 3
        mock_cmd2 = Mock()
        mock_cmd2.order = 1
        mock_cmd3 = Mock()
        mock_cmd3.order = 2

        creator.commands = [mock_cmd1, mock_cmd2, mock_cmd3]
        creator.order_commands(reverse=False)

        assert creator.commands[0].order == 1
        assert creator.commands[1].order == 2
        assert creator.commands[2].order == 3

    def test_execute_commands_calls_function_on_all_commands(self, creator):
        mock_cmd1 = Mock()
        mock_cmd2 = Mock()
        creator.commands = [mock_cmd1, mock_cmd2]

        creator.execute_commands("pre_command")

        mock_cmd1.pre_command.assert_called_once()
        mock_cmd2.pre_command.assert_called_once()

    @patch("icon_manager.content.controller.desktop.get_commands")
    def test_write_executes_full_workflow(self, mock_get_commands, creator):
        mock_folder = Mock(spec=MatchedRuleFolder)
        mock_folder.desktop_ini = Mock(spec=DesktopIniFile)
        mock_folder.icon_path_for_desktop_ini.return_value = "icon.ico"

        mock_commands = [Mock(), Mock()]
        for i, cmd in enumerate(mock_commands):
            cmd.order = i + 1
        mock_get_commands.return_value = mock_commands

        creator.write(mock_folder, True)

        # Verify workflow execution
        mock_get_commands.assert_called_once_with(mock_folder, True)
        creator.source.write.assert_called_once()

        # Verify commands were executed
        for cmd in mock_commands:
            cmd.pre_command.assert_called_once()
            cmd.post_command.assert_called_once()
