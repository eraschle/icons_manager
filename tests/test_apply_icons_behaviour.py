"""The whole job, end to end: rules in, desktop.ini out.

A folder gets a Windows icon by having a ``desktop.ini`` whose
``IconResource`` points at an .ico file. These tests run the real service on
a real tree and read that file back, so they cover crawling, matching,
writing, cataloguing and deleting together.

The ``attrib`` calls that mark the files hidden only work on Windows; they
go through ``os.system``, so elsewhere they fail without raising and without
touching the file contents asserted here.
"""

import configparser
from pathlib import Path

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.interfaces.path import IconSearchFolder, SearchFolder
from icon_manager.library.controller import IconLibraryController
from icon_manager.rules.manager import ExcludeManager
from icon_manager.services.config_service import ConfigService
from tests.conftest import add_icon, exclude_manager, make_tree


def build_service(user_config: UserConfig, exclude: ExcludeManager | None = None) -> ConfigService:
    service = ConfigService(
        user_config,
        settings=IconLibraryController(user_config),
        desktop=DesktopIniController(user_config),
        icon_folders=IconFolderController(user_config),
        icon_files=IconFileController(user_config),
        rules=RulesApplyController(user_config),
    )
    service.create_settings()
    service.update_before_and_after([])
    service.set_exclude_manager(exclude if exclude is not None else ExcludeManager([]))
    return service


def icon_resource(folder: Path) -> str:
    """The IconResource value of ``folder``'s desktop.ini."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(folder / "desktop.ini", encoding="utf-8")
    return parser[".ShellClassInfo"]["IconResource"]


def folders_with_icon(workspace: Path) -> set[str]:
    return {ini.parent.name for ini in workspace.rglob("desktop.ini")}


class TestApplyingIcons:
    def test_a_matching_folder_gets_a_desktop_ini_pointing_at_the_icon(
        self, user_config: UserConfig, library: Path, workspace: Path
    ):
        icon = add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["docs/", "music/"])

        build_service(user_config).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"docs"}
        assert icon_resource(workspace / "docs") == f"{icon},0"

    def test_a_folder_matching_no_rule_is_left_alone(self, user_config: UserConfig, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["music/", "photos/"])

        build_service(user_config).find_and_apply_matches()

        assert folders_with_icon(workspace) == set()

    def test_an_icon_without_a_config_file_applies_to_nothing(
        self, user_config: UserConfig, library: Path, workspace: Path
    ):
        (library / "orphan.ico").write_bytes(b"\x00\x00\x01\x00")
        make_tree(workspace, ["orphan/"])

        build_service(user_config).find_and_apply_matches()

        assert folders_with_icon(workspace) == set()

    def test_nested_folders_are_matched_too(self, user_config: UserConfig, library: Path, workspace: Path):
        add_icon(library, "src", name={"rules": [{"equals": ["src"]}]})
        make_tree(workspace, ["a/b/src/", "c/src/", "d/"])

        build_service(user_config).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"src"}
        assert len(list(workspace.rglob("desktop.ini"))) == 2

    def test_the_lower_order_wins_when_two_icons_match(self, user_config: UserConfig, library: Path, workspace: Path):
        # order is the tie breaker; 1 is applied before the default 5
        add_icon(library, "specific", name={"rules": [{"equals": ["docs"]}]})
        specific = library / "specific.json"
        specific.write_text(specific.read_text().replace('"order": 5', '"order": 1'), encoding="utf-8")
        add_icon(library, "general", name={"rules": [{"contains": ["doc"]}]})
        make_tree(workspace, ["docs/"])

        build_service(user_config).find_and_apply_matches()

        assert icon_resource(workspace / "docs") == f"{library / 'specific.ico'},0"

    def test_an_order_above_99_still_sorts_as_a_number(self, user_config: UserConfig, library: Path, workspace: Path):
        # the order was sorted as a zero-padded two-digit string, so "100"
        # sorted before "20" and the wrong icon won
        for name, order in (("first", 20), ("second", 100)):
            add_icon(library, name, name={"rules": [{"equals": ["docs"]}]})
            config = library / f"{name}.json"
            config.write_text(config.read_text().replace('"order": 5', f'"order": {order}'), encoding="utf-8")
        make_tree(workspace, ["docs/"])

        build_service(user_config).find_and_apply_matches()

        assert icon_resource(workspace / "docs") == f"{library / 'first.ico'},0"


class TestCopyingTheIcon:
    def test_the_icon_is_copied_into_a_hidden_icon_folder_when_asked(self, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["docs/"])
        config = UserConfig(
            name="copying",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=True)],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=True,
        )

        build_service(config).find_and_apply_matches()

        copied = workspace / "docs" / "__icon__" / "docs.ico"
        assert copied.is_file()
        # a copied icon is referenced relative to the folder, so the icon
        # survives the folder being moved
        assert icon_resource(workspace / "docs") == f"{Path('__icon__') / 'docs.ico'},0"

    def test_the_icon_is_referenced_from_the_library_when_not_copying(
        self, user_config: UserConfig, library: Path, workspace: Path
    ):
        icon = add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["docs/"])

        build_service(user_config).find_and_apply_matches()

        assert not (workspace / "docs" / "__icon__").exists()
        assert icon_resource(workspace / "docs") == f"{icon},0"


class TestExcluding:
    def test_an_exclude_rule_keeps_a_matching_folder_out(
        self, user_config: UserConfig, library: Path, workspace: Path, tmp_path: Path
    ):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["keep/docs/", "skip/docs/"])
        exclude = exclude_manager(tmp_path / "exclude.config", {"name": {"rules": [{"equals": ["skip"]}]}})

        build_service(user_config, exclude).find_and_apply_matches()

        assert (workspace / "keep" / "docs" / "desktop.ini").is_file()
        assert not (workspace / "skip" / "docs" / "desktop.ini").exists()

    def test_an_excluded_folder_name_is_not_searched(self, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["obj/docs/", "real/docs/"])
        config = UserConfig(
            name="excluding",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
            code_folders=[],
            exclude_folders=["obj"],
            before_or_after=[],
            copy_icon=False,
        )

        build_service(config).find_and_apply_matches()

        assert (workspace / "real" / "docs" / "desktop.ini").is_file()
        assert not (workspace / "obj" / "docs" / "desktop.ini").exists()


class TestWhatExcludingMeans:
    """Pinned because the three mechanisms differ, and silently.

    All three mean "do not search inside this folder"; none of them except
    code_folders makes the folder itself ineligible for an icon. If that is
    not what you want from an exclude rule, this is the test to change.
    """

    def test_a_folder_matching_an_exclude_rule_can_still_get_its_own_icon(
        self, user_config: UserConfig, library: Path, workspace: Path, tmp_path: Path
    ):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs", "sub"]}]})
        make_tree(workspace, ["docs/sub/"])
        exclude = exclude_manager(tmp_path / "exclude.config", {"name": {"rules": [{"equals": ["docs"]}]}})

        build_service(user_config, exclude).find_and_apply_matches()

        assert (workspace / "docs" / "desktop.ini").is_file()
        assert not (workspace / "docs" / "sub" / "desktop.ini").exists()

    def test_an_excluded_folder_name_can_still_get_its_own_icon(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["obj", "sub"]}]})
        make_tree(workspace, ["obj/sub/"])
        config = UserConfig(
            name="excluding",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
            code_folders=[],
            exclude_folders=["obj"],
            before_or_after=[],
            copy_icon=False,
        )

        build_service(config).find_and_apply_matches()

        assert (workspace / "obj" / "desktop.ini").is_file()
        assert not (workspace / "obj" / "sub" / "desktop.ini").exists()

    def test_a_code_folder_stops_the_search_below_it(self, library: Path, workspace: Path):
        # code_folders is also what stops the walk at the top of a repository:
        # a folder whose sibling is a code folder is not descended into
        add_icon(library, "icon", name={"rules": [{"equals": [".git", "src", "deep"]}]})
        make_tree(workspace, [".git/hooks/", "src/deep/"])
        config = UserConfig(
            name="project",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
            code_folders=[".git"],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )

        build_service(config).find_and_apply_matches()

        assert not (workspace / "src" / "deep" / "desktop.ini").exists()

    def test_a_code_folder_itself_is_still_matched(self, library: Path, workspace: Path):
        # Surprising, and pinned so it is a decision rather than an accident:
        # _is_project() would drop the folder, but _is_clean_recursive() is
        # checked first and always matches a code folder, because a folder is
        # in its own parent's folder list. So .git can get an icon, which is
        # why RuleFolderCommand has its own Git check before setting
        # attributes. Change filters.filter_folder if that is not wanted.
        add_icon(library, "icon", name={"rules": [{"equals": [".git"]}]})
        make_tree(workspace, [".git/hooks/"])
        config = UserConfig(
            name="project",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
            code_folders=[".git"],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )

        build_service(config).find_and_apply_matches()

        assert folders_with_icon(workspace) == {".git"}


class TestDeletingAndReApplying:
    def test_delete_removes_what_apply_wrote(self, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["docs/"])
        config = UserConfig(
            name="roundtrip",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=True)],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=True,
        )

        build_service(config).find_and_apply_matches()
        assert (workspace / "docs" / "desktop.ini").is_file()

        cleanup = build_service(config)
        cleanup.find_existing_content()
        cleanup.delete_content()

        assert not (workspace / "docs" / "desktop.ini").exists()
        assert not (workspace / "docs" / "__icon__").exists()

    def test_delete_leaves_a_foreign_desktop_ini_alone(self, user_config: UserConfig, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["other/"])
        foreign = workspace / "other" / "desktop.ini"
        foreign.write_text("[.ShellClassInfo]\nIconResource=C:\\somewhere\\else.ico,0\n", encoding="utf-8")

        service = build_service(user_config)
        service.find_existing_content()
        service.delete_content()

        assert foreign.is_file(), "only desktop.ini files written by this tool may be deleted"

    def test_re_apply_restores_a_lost_desktop_ini_from_the_copied_icon(self, library: Path, workspace: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        make_tree(workspace, ["docs/"])
        config = UserConfig(
            name="reapply",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(workspace), copy_icon=True)],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=True,
        )
        build_service(config).find_and_apply_matches()
        (workspace / "docs" / "desktop.ini").unlink()

        restored = build_service(config)
        restored.find_existing_content()
        restored.re_apply_icons()

        assert (workspace / "docs" / "desktop.ini").is_file()
        assert icon_resource(workspace / "docs") == f"{Path('__icon__') / 'docs.ico'},0"


class TestUserConfigurationsAreIndependent:
    """Regression test: builders used to be shared via default arguments."""

    def test_two_configurations_use_their_own_library(self, tmp_path: Path):
        first_library, second_library = tmp_path / "lib_a", tmp_path / "lib_b"
        first_space, second_space = tmp_path / "space_a", tmp_path / "space_b"
        add_icon(first_library, "alpha", name={"rules": [{"equals": ["target"]}]})
        add_icon(second_library, "beta", name={"rules": [{"equals": ["target"]}]})
        make_tree(first_space, ["target/"])
        make_tree(second_space, ["target/"])

        for library_path, space in ((first_library, first_space), (second_library, second_space)):
            config = UserConfig(
                name=library_path.name,
                icons_path=SearchFolder(str(library_path)),
                search_folders=[IconSearchFolder(str(space), copy_icon=False)],
                code_folders=[],
                exclude_folders=[],
                before_or_after=[],
                copy_icon=False,
            )
            build_service(config).find_and_apply_matches()

        assert icon_resource(first_space / "target") == f"{first_library / 'alpha.ico'},0"
        assert icon_resource(second_space / "target") == f"{second_library / 'beta.ico'},0"
