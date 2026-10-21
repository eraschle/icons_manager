"""What each rule type actually matches, against a real folder tree.

The rules are the user-facing contract: a config file says "name equals
docs" and a folder either gets the icon or it does not. These tests go
through the real factory, so a change to the config format or to the rule
classes shows up here.
"""

from pathlib import Path

import pytest

from icon_manager.crawler.crawler import crawling_folders
from icon_manager.interfaces.path import Folder, IconSearchFolder
from icon_manager.rules.base import Rule
from icon_manager.rules.mapping import rule_mapping
from tests.conftest import make_tree, rule_manager


def crawl(root: Path) -> Folder:
    return crawling_folders([IconSearchFolder(str(root), copy_icon=False)])[0]


def folder_named(tree: Folder, name: str) -> Folder:
    for folder in tree.folders:
        if folder.name == name:
            return folder
        try:
            return folder_named(folder, name)
        except LookupError:
            continue
    raise LookupError(f'No folder "{name}" below {tree.path}')


def matching_names(manager, tree: Folder) -> list[str]:
    """The names of all folders below ``tree`` that ``manager`` matches."""
    matched = []
    for folder in tree.folders:
        if manager.is_allowed(folder):
            matched.append(folder.name)
        matched.extend(matching_names(manager, folder))
    return matched


@pytest.fixture
def tree(workspace: Path) -> Folder:
    make_tree(
        workspace,
        [
            "docs/readme.md",
            "documents/notes.txt",
            "my-docs/a.txt",
            "Docs-Upper/b.txt",
            "project/src/main.py",
            "project/.git/config",
            "photos/holiday.jpg",
            "music/",
        ],
    )
    return crawl(workspace)


class TestEveryRuleNameIsImplemented:
    def test_mapping_covers_every_rule_but_unknown(self):
        mapped = rule_mapping()
        expected = {rule for rule in Rule if rule is not Rule.UNKNOWN}

        assert set(mapped) == expected

    def test_every_mapped_rule_can_be_built_from_a_config(self, library: Path, tree: Folder):
        # A rule the factory cannot build would otherwise only surface when a
        # user puts it in a config file.
        for rule in rule_mapping():
            if rule is Rule.CHAINED:
                values = [{"equals": ["docs"]}]
            elif rule in (Rule.CONTAINS_FILE, Rule.NOT_CONTAINS_FILE):
                values = ["md"]
            elif rule in (Rule.CONTAINS_FOLDER, Rule.NOT_CONTAINS_FOLDER):
                values = ["src"]
            else:
                values = ["docs"]

            manager = rule_manager(library, f"icon_{rule.value}", name={"rules": [{rule.value: values}]})
            manager.setup_rules([])

            assert isinstance(manager.is_allowed(tree.folders[0]), bool), rule


class TestNameRules:
    def test_equals_matches_only_the_exact_name(self, library: Path, tree: Folder):
        manager = rule_manager(library, "exact", name={"rules": [{"equals": ["docs"]}]})
        manager.setup_rules([])

        assert matching_names(manager, tree) == ["docs"]

    def test_equals_ignores_case_by_default(self, library: Path, tree: Folder):
        manager = rule_manager(library, "upper", name={"rules": [{"equals": ["docs-upper"]}]})
        manager.setup_rules([])

        assert matching_names(manager, tree) == ["Docs-Upper"]

    def test_equals_respects_case_when_asked(self, library: Path, tree: Folder):
        manager = rule_manager(library, "cased", name={"rules": [{"equals": ["docs-upper"], "case_sensitive": True}]})
        manager.setup_rules([])

        assert matching_names(manager, tree) == []

    def test_starts_with_matches_the_prefix(self, library: Path, tree: Folder):
        manager = rule_manager(library, "prefix", name={"rules": [{"starts_with": ["doc"]}]})
        manager.setup_rules([])

        assert sorted(matching_names(manager, tree)) == ["Docs-Upper", "docs", "documents"]

    def test_ends_with_matches_the_suffix(self, library: Path, tree: Folder):
        manager = rule_manager(library, "suffix", name={"rules": [{"ends_with": ["docs"]}]})
        manager.setup_rules([])

        # "docs" itself ends with "docs"
        assert sorted(matching_names(manager, tree)) == ["docs", "my-docs"]

    def test_contains_matches_anywhere_in_the_name(self, library: Path, tree: Folder):
        manager = rule_manager(library, "infix", name={"rules": [{"contains": ["doc"]}]})
        manager.setup_rules([])

        assert sorted(matching_names(manager, tree)) == ["Docs-Upper", "docs", "documents", "my-docs"]

    def test_not_equals_matches_every_other_folder(self, library: Path, tree: Folder):
        manager = rule_manager(library, "inverse", name={"rules": [{"not_equals": ["docs"]}]})
        manager.setup_rules([])

        matched = matching_names(manager, tree)

        assert "docs" not in matched
        assert "music" in matched

    def test_several_values_match_any_of_them_by_default(self, library: Path, tree: Folder):
        manager = rule_manager(library, "any", name={"rules": [{"equals": ["docs", "music"]}]})
        manager.setup_rules([])

        assert sorted(matching_names(manager, tree)) == ["docs", "music"]


class TestBeforeOrAfterAffixes:
    """``before_or_after`` lets "docs" also match "_docs", "docs_", "_docs_"."""

    def test_affixes_are_not_applied_unless_requested(self, workspace: Path, library: Path):
        make_tree(workspace, ["_docs/", "docs/"])
        tree = crawl(workspace)
        manager = rule_manager(library, "plain", name={"rules": [{"equals": ["docs"]}]})
        manager.setup_rules(["_"])

        assert matching_names(manager, tree) == ["docs"]

    def test_affixes_match_before_and_after_the_value(self, workspace: Path, library: Path):
        make_tree(workspace, ["_docs/", "docs_/", "_docs_/", "docs/", "xdocs/"])
        tree = crawl(workspace)
        manager = rule_manager(library, "affixed", name={"rules": [{"equals": ["docs"], "before_or_after": True}]})
        manager.setup_rules(["_"])

        assert sorted(matching_names(manager, tree)) == ["_docs", "_docs_", "docs", "docs_"]


class TestContentRules:
    def test_contains_file_matches_by_extension(self, library: Path, tree: Folder):
        manager = rule_manager(library, "markdown", path={"rules": [{"contains_file": ["md"]}]})
        manager.setup_rules([])

        assert matching_names(manager, tree) == ["docs"]

    def test_contains_folder_matches_by_child_folder_name(self, library: Path, tree: Folder):
        manager = rule_manager(library, "sourced", path={"rules": [{"contains_folder": ["src"]}]})
        manager.setup_rules([])

        assert matching_names(manager, tree) == ["project"]

    def test_contains_folder_searches_deeper_with_a_higher_level(self, workspace: Path, library: Path):
        make_tree(workspace, ["repo/nested/deep/src/"])
        tree = crawl(workspace)

        shallow = rule_manager(library, "shallow", path={"rules": [{"contains_folder": ["src"], "level": 1}]})
        shallow.setup_rules([])
        deep = rule_manager(library, "deep", path={"rules": [{"contains_folder": ["src"], "level": 4}]})
        deep.setup_rules([])

        assert "repo" not in matching_names(shallow, tree)
        assert "repo" in matching_names(deep, tree)


class TestChainedRules:
    def test_all_operator_requires_every_chained_rule(self, library: Path, tree: Folder):
        manager = rule_manager(
            library,
            "both",
            name={
                "rules": [
                    {
                        "chained": [{"starts_with": ["doc"]}, {"ends_with": ["ents"]}],
                        "operator": "all",
                    }
                ]
            },
        )
        manager.setup_rules([])

        assert matching_names(manager, tree) == ["documents"]

    def test_any_operator_requires_only_one(self, library: Path, tree: Folder):
        manager = rule_manager(
            library,
            "either",
            name={
                "rules": [
                    {
                        "chained": [{"equals": ["music"]}, {"equals": ["photos"]}],
                        "operator": "any",
                    }
                ]
            },
        )
        manager.setup_rules([])

        assert sorted(matching_names(manager, tree)) == ["music", "photos"]


class TestEmptyRules:
    def test_a_config_without_rules_is_empty_and_matches_nothing(self, library: Path, tree: Folder):
        manager = rule_manager(library, "blank", name={"rules": []})
        manager.setup_rules([])

        assert manager.is_empty()
        assert matching_names(manager, tree) == []
