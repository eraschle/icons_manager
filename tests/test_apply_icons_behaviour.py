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

import pytest

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


def project_config(library: Path, workspace: Path, *, markers=(".git", ".venv"), skip=(), depth: int = 1) -> UserConfig:
    return UserConfig(
        name="project",
        icons_path=SearchFolder(str(library)),
        search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
        code_folders=list(markers),
        exclude_folders=list(skip),
        before_or_after=[],
        copy_icon=False,
        project_depth=depth,
    )


class TestTheThreeOutcomes:
    """SKIP, LEAF and SEARCH, the whole filtering contract.

    - ``exclude_folders`` and ``code_folders``: no icon, never searched.
    - a folder containing a marker is a project: searched ``project_depth``
      levels deep, so its direct children can still get an icon.
    - everything else: icon, and searched all the way down.
    """

    def test_an_excluded_folder_gets_no_icon_and_is_not_searched(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["obj", "sub"]}]})
        make_tree(workspace, ["obj/sub/"])

        build_service(project_config(library, workspace, skip=["obj"])).find_and_apply_matches()

        assert folders_with_icon(workspace) == set()

    def test_a_marker_folder_gets_no_icon_either(self, library: Path, workspace: Path):
        # .git used to get one, which is why RuleFolderCommand still carries
        # its own .git check before setting attributes
        add_icon(library, "icon", name={"rules": [{"equals": [".git", "hooks"]}]})
        make_tree(workspace, ["repo/.git/hooks/"])

        build_service(project_config(library, workspace)).find_and_apply_matches()

        assert folders_with_icon(workspace) == set()

    def test_a_project_is_searched_one_level_by_default(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["repo", "docs", "api", "deep"]}]})
        make_tree(workspace, ["repo/.git/", "repo/docs/api/", "repo/src/deep/"])

        build_service(project_config(library, workspace)).find_and_apply_matches()

        # the project and its direct children, nothing below them
        assert folders_with_icon(workspace) == {"repo", "docs"}

    def test_project_depth_zero_makes_the_project_a_leaf(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["repo", "docs"]}]})
        make_tree(workspace, ["repo/.git/", "repo/docs/"])

        build_service(project_config(library, workspace, depth=0)).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"repo"}

    def test_a_higher_project_depth_reaches_further(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["repo", "docs", "api"]}]})
        make_tree(workspace, ["repo/.git/", "repo/docs/api/"])

        build_service(project_config(library, workspace, depth=2)).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"repo", "docs", "api"}

    def test_a_folder_without_a_marker_is_searched_all_the_way_down(self, library: Path, workspace: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["plain", "child", "grandchild"]}]})
        make_tree(workspace, ["plain/child/grandchild/"])

        build_service(project_config(library, workspace)).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"plain", "child", "grandchild"}

    def test_a_stray_marker_does_not_limit_its_siblings(self, library: Path, workspace: Path):
        # the predicate this replaces looked at an entry's siblings, so one
        # .venv on a level stopped the search for every folder on that level
        add_icon(library, "icon", name={"rules": [{"equals": ["plain", "child"]}]})
        make_tree(workspace, ["repo/.venv/", "plain/child/"])

        build_service(project_config(library, workspace)).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"plain", "child"}


class TestExcludeRuleActions:
    """Each section of excluded_rules.config carries its own action."""

    def test_the_default_action_skips_the_folder_and_its_children(
        self, user_config: UserConfig, library: Path, workspace: Path, tmp_path: Path
    ):
        add_icon(library, "icon", name={"rules": [{"equals": ["backup", "old"]}]})
        make_tree(workspace, ["backup/old/"])
        exclude = exclude_manager(tmp_path / "e.config", {"name": {"rules": [{"equals": ["backup"]}]}})

        build_service(user_config, exclude).find_and_apply_matches()

        assert folders_with_icon(workspace) == set()

    def test_the_leaf_action_keeps_the_icon_and_stops_below_it(
        self, user_config: UserConfig, library: Path, workspace: Path, tmp_path: Path
    ):
        add_icon(library, "icon", name={"rules": [{"equals": ["backup", "old"]}]})
        make_tree(workspace, ["backup/old/"])
        exclude = exclude_manager(
            tmp_path / "e.config", {"action": "leaf", "name": {"rules": [{"equals": ["backup"]}]}}
        )

        build_service(user_config, exclude).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"backup"}

    def test_a_parent_name_rule_still_works_as_before(
        self, user_config: UserConfig, library: Path, workspace: Path, tmp_path: Path
    ):
        # the idiom the old semantics forced: match the children to stop the
        # search inside their parent. It keeps working - the parent gets an
        # icon because nothing matched it, and its children are skipped.
        add_icon(library, "icon", name={"rules": [{"equals": ["backup", "old"]}]})
        make_tree(workspace, ["backup/old/"])
        exclude = exclude_manager(tmp_path / "e.config", {"parent_name": {"rules": [{"equals": ["backup"]}]}})

        build_service(user_config, exclude).find_and_apply_matches()

        assert folders_with_icon(workspace) == {"backup"}

    def test_an_unknown_action_is_rejected(self, tmp_path: Path):
        with pytest.raises(ValueError, match="is not an action"):
            exclude_manager(tmp_path / "e.config", {"action": "nonsense", "name": {"rules": []}})

    def test_search_is_not_a_valid_exclude_action(self, tmp_path: Path):
        with pytest.raises(ValueError, match="is not an action"):
            exclude_manager(tmp_path / "e.config", {"action": "search", "name": {"rules": []}})


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
