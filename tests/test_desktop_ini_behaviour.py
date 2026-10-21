"""The desktop.ini file itself: its content, and who may touch it.

A desktop.ini written by this tool carries an ``IconManager=1`` marker. That
marker is the whole safety mechanism: it is what keeps the tool from
overwriting or deleting a desktop.ini that Windows or another program wrote.
"""

from pathlib import Path

import pytest

from icon_manager.content.controller.desktop import (
    DesktopFileChecker,
    DesktopIniBuilder,
    DesktopIniCommand,
    DesktopIniCreator,
    IconFileCommand,
    IconFolderCommand,
    RuleFolderCommand,
    get_commands,
)
from icon_manager.content.models.desktop import DesktopIniFile, Git
from icon_manager.content.models.matched import MatchedIconFolder, MatchedRuleFolder
from icon_manager.crawler.crawler import crawling_icons
from icon_manager.data.ini_source import DesktopFileSource
from icon_manager.interfaces.path import FolderModel
from icon_manager.library.controller import IconLibraryController
from icon_manager.library.models import IconSetting, LibraryIconFile
from tests.conftest import add_icon


@pytest.fixture
def setting(user_config, library: Path) -> IconSetting:
    add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
    controller = IconLibraryController(user_config)
    controller.create_settings(crawling_icons(user_config.icons_path, IconLibraryController.icons_extensions))
    return controller.settings()[0]


@pytest.fixture
def rule_folder(setting: IconSetting, workspace: Path) -> MatchedRuleFolder:
    target = workspace / "docs"
    target.mkdir()
    return MatchedRuleFolder(FolderModel(str(target)), setting)


class TestTheWrittenContent:
    def test_it_points_at_the_icon_and_carries_the_marker(self, rule_folder: MatchedRuleFolder):
        lines = list(DesktopIniCreator().create_content(rule_folder))

        assert lines[0] == "[.ShellClassInfo]"
        assert lines[1] == f"IconResource={rule_folder.library_icon.path},0"
        assert DesktopIniBuilder.app_entry in lines
        assert "[ViewState]" in lines

    def test_writing_it_produces_a_file_the_checker_recognises(self, rule_folder: MatchedRuleFolder):
        source = DesktopFileSource()
        source.write(rule_folder.desktop_ini, DesktopIniCreator().create_content(rule_folder))

        assert DesktopFileChecker(source).is_app_file(rule_folder.desktop_ini)

    def test_a_copied_icon_is_referenced_relative_to_the_folder(self, rule_folder: MatchedRuleFolder):
        rule_folder.icon_folder.create()
        rule_folder.library_icon.copy_to(rule_folder.local_icon)

        assert rule_folder.icon_path_for_desktop_ini() == str(Path("__icon__") / "docs.ico")

    def test_an_uncopied_icon_is_referenced_by_its_library_path(self, rule_folder: MatchedRuleFolder):
        assert rule_folder.icon_path_for_desktop_ini() == rule_folder.library_icon.path


class TestWhoMayWrite:
    def test_a_folder_without_a_desktop_ini_may_be_written(self, rule_folder: MatchedRuleFolder):
        assert DesktopIniCreator().can_write(rule_folder.desktop_ini)

    def test_our_own_desktop_ini_may_be_overwritten(self, rule_folder: MatchedRuleFolder):
        creator = DesktopIniCreator()
        DesktopFileSource().write(rule_folder.desktop_ini, creator.create_content(rule_folder))

        assert creator.can_write(rule_folder.desktop_ini)

    def test_a_foreign_desktop_ini_is_refused(self, workspace: Path):
        foreign = workspace / "desktop.ini"
        foreign.write_text("[.ShellClassInfo]\nIconResource=C:\\other.ico,0\n", encoding="utf-8")

        assert not DesktopIniCreator().can_write(DesktopIniFile(str(foreign)))

    def test_the_checker_reads_an_empty_file_as_foreign(self, workspace: Path):
        empty = workspace / "desktop.ini"
        empty.touch()

        assert not DesktopFileChecker(DesktopFileSource()).is_app_file(DesktopIniFile(str(empty)))


class TestRecognisingPaths:
    @pytest.mark.parametrize("path", ["C:/x/desktop.ini", "/home/u/desktop.ini"])
    def test_a_desktop_ini_is_recognised_by_name(self, path: str):
        assert DesktopIniFile.is_model(path)

    def test_another_ini_is_not(self):
        assert not DesktopIniFile.is_model("/home/u/settings.ini")

    def test_a_git_folder_is_recognised(self):
        assert Git.is_model("/home/u/project/.git")
        assert not Git.is_model("/home/u/project/src")

    def test_an_icon_folder_is_recognised_by_name(self):
        assert MatchedIconFolder.is_model(f"/home/u/docs/{MatchedIconFolder.folder_name}")
        assert not MatchedIconFolder.is_model("/home/u/docs/icons")


class TestCommandOrder:
    """The commands wrap the write: attributes off before, on again after."""

    def test_the_four_commands_are_created_in_order(self, rule_folder: MatchedRuleFolder):
        commands = get_commands(rule_folder, copy_icon=True)

        assert [type(command) for command in commands] == [
            RuleFolderCommand,
            IconFolderCommand,
            IconFileCommand,
            DesktopIniCommand,
        ]
        assert [command.order for command in commands] == [1, 2, 3, 4]

    def test_pre_commands_run_outside_in_and_post_commands_inside_out(self, rule_folder: MatchedRuleFolder):
        creator = DesktopIniCreator()
        commands = get_commands(rule_folder, copy_icon=True)

        creator.order_commands(commands, reverse=False)
        assert [command.order for command in commands] == [1, 2, 3, 4]

        creator.order_commands(commands, reverse=True)
        assert [command.order for command in commands] == [4, 3, 2, 1]

    def test_a_git_folder_is_never_given_an_icon_attribute(self, setting: IconSetting, workspace: Path):
        git_folder = workspace / ".git"
        git_folder.mkdir()
        command = RuleFolderCommand(1, True, MatchedRuleFolder(FolderModel(str(git_folder)), setting))

        assert not command.can_change_attribute()


class TestTheWriteItself:
    def test_it_creates_the_icon_folder_and_copies_the_icon_when_copying(self, rule_folder: MatchedRuleFolder):
        DesktopIniCreator().write(rule_folder, copy_icon=True)

        assert rule_folder.desktop_ini.exists()
        assert rule_folder.icon_folder.exists()
        assert rule_folder.local_icon.exists()

    def test_it_writes_only_the_desktop_ini_when_not_copying(self, rule_folder: MatchedRuleFolder):
        DesktopIniCreator().write(rule_folder, copy_icon=False)

        assert rule_folder.desktop_ini.exists()
        assert not rule_folder.icon_folder.exists()

    def test_the_library_icon_is_left_in_place(self, rule_folder: MatchedRuleFolder):
        library_icon: LibraryIconFile = rule_folder.library_icon

        DesktopIniCreator().write(rule_folder, copy_icon=True)

        assert library_icon.exists()
