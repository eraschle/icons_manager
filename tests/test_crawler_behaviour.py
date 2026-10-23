"""The crawler must not read what the filter would throw away.

The filter used to run on the finished tree, so ``exclude_folders``,
``code_folders`` and ``project_depth`` saved no I/O at all: a
``node_modules`` was crawled in full and then discarded. These tests count
the actual directory reads, because "it still produces the right tree" was
true before as well - what changed is the cost.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from icon_manager.crawler.crawler import crawl_search_folders, crawling_folders
from icon_manager.crawler.options import FilterOptions
from icon_manager.interfaces.path import Folder, IconSearchFolder
from icon_manager.rules.manager import ExcludeManager
from tests.conftest import exclude_manager, make_tree


class ScandirCounter:
    """Counts os.scandir calls, i.e. how many folders were actually read."""

    def __init__(self) -> None:
        self.paths: list[str] = []

    def __call__(self, path) -> Iterator[os.DirEntry]:
        self.paths.append(str(path))
        return self._real(path)

    _real = staticmethod(os.scandir)

    @property
    def count(self) -> int:
        return len(self.paths)

    def read(self, name: str) -> bool:
        return any(Path(p).name == name for p in self.paths)


@pytest.fixture
def counter(monkeypatch) -> ScandirCounter:
    counting = ScandirCounter()
    monkeypatch.setattr(os, "scandir", counting)
    return counting


def options(**kwargs) -> FilterOptions:
    kwargs.setdefault("exclude", ExcludeManager([]))
    return FilterOptions(**kwargs)


def folder_names(folders: list[Folder]) -> set[str]:
    """The folders the icon rules are offered, i.e. the unmarked ones.

    A leaf's children stay attached but marked excluded, so a
    contains_folder rule can read their names while the rules skip them -
    which is what the builder does, and what this mirrors.
    """
    found = set()
    for folder in folders:
        if folder.excluded:
            continue
        found.add(folder.name)
        found |= folder_names(folder.folders)
    return found


def attached_names(folders: list[Folder]) -> set[str]:
    """Every folder in the tree, marked or not."""
    found = set()
    for folder in folders:
        found.add(folder.name)
        found |= attached_names(folder.folders)
    return found


def crawl(workspace: Path, opts: FilterOptions) -> list[Folder]:
    return crawl_search_folders("test", [IconSearchFolder(str(workspace), copy_icon=False)], opts)


class TestSkippedFoldersAreNeverRead:
    def test_a_skipped_folder_is_not_opened_at_all(self, workspace: Path, counter: ScandirCounter):
        make_tree(workspace, ["keep/sub/", "node_modules/a/b/c/"])

        crawl(workspace, options(skip_names=["node_modules"]))

        assert not counter.read("node_modules"), "the folder itself must not be read"
        assert counter.read("keep")

    def test_the_full_crawl_does_read_it(self, workspace: Path, counter: ScandirCounter):
        make_tree(workspace, ["keep/sub/", "node_modules/a/b/c/"])

        crawling_folders([IconSearchFolder(str(workspace), copy_icon=False)])

        assert counter.read("node_modules"), "this is what the filter used to cost"

    def test_a_deep_skipped_subtree_costs_one_read_per_parent(self, workspace: Path, counter: ScandirCounter):
        make_tree(workspace, [f"project/node_modules/pkg{n}/a/b/" for n in range(20)])

        crawl(workspace, options(skip_names=["node_modules"]))

        # the workspace and project, nothing below
        assert counter.count == 2


class TestProjectDepthStopsTheWalk:
    def test_nothing_below_the_project_depth_is_read(self, workspace: Path, counter: ScandirCounter):
        make_tree(workspace, ["repo/.git/", "repo/src/deep/deeper/"])

        crawl(workspace, options(skip_names=[".git"], project_markers=[".git"], project_depth=1))

        assert counter.read("src"), "a direct child of the project is still offered"
        assert not counter.read("deep"), "below the project depth nothing is read"

    def test_depth_zero_reads_only_the_project_itself(self, workspace: Path, counter: ScandirCounter):
        make_tree(workspace, ["repo/.git/", "repo/src/deep/"])

        crawl(workspace, options(skip_names=[".git"], project_markers=[".git"], project_depth=0))

        assert not counter.read("src")

    def test_a_marker_is_seen_even_though_it_is_skipped(self, workspace: Path):
        # .git is both the marker that makes repo a project and a skipped
        # name. Dropping skipped folders before the decision would hide it,
        # and nothing would ever be recognised as a project.
        make_tree(workspace, ["repo/.git/", "repo/src/deep/"])

        crawled = crawl(workspace, options(skip_names=[".git"], project_markers=[".git"], project_depth=1))

        assert "src" in folder_names(crawled)
        assert "deep" not in folder_names(crawled), "below the project depth, nothing is offered"
        assert "deep" in attached_names(crawled), "but its name stays readable for contains_folder"


class TestExcludeRulesPruneTheWalkToo:
    def test_a_skip_rule_stops_the_walk(self, workspace: Path, counter: ScandirCounter, tmp_path: Path):
        make_tree(workspace, ["keep/sub/", "drop/a/b/"])
        exclude = exclude_manager(tmp_path / "e.config", {"name": {"rules": [{"equals": ["drop"]}]}})
        exclude.setup_rules([])

        crawl(workspace, options(exclude=exclude))

        # drop is read once to decide, its children are not
        assert counter.read("drop")
        assert not counter.read("a")
        assert counter.read("sub")

    def test_a_leaf_rule_stops_the_walk(self, workspace: Path, counter: ScandirCounter, tmp_path: Path):
        make_tree(workspace, ["backup/old/tief/"])
        exclude = exclude_manager(
            tmp_path / "e.config", {"action": "leaf", "name": {"rules": [{"equals": ["backup"]}]}}
        )
        exclude.setup_rules([])

        crawled = crawl(workspace, options(exclude=exclude))

        assert "backup" in folder_names(crawled)
        assert not counter.read("old")


class TestWhatTheRulesCanStillSee:
    """Pruning must not change what a rule sees, only what it costs."""

    def test_a_contains_folder_rule_at_level_one_sees_the_children(self, workspace: Path, tmp_path: Path):
        make_tree(workspace, ["repo/.git/", "repo/marker/"])
        exclude = exclude_manager(
            tmp_path / "e.config",
            {"path": {"rules": [{"contains_folder": ["marker"], "level": 1}]}},
        )
        exclude.setup_rules([])

        crawled = crawl(workspace, options(exclude=exclude))

        assert "repo" not in folder_names(crawled), "the rule matched, so repo is skipped"

    def test_inspect_depth_is_taken_from_the_rules(self, tmp_path: Path):
        exclude = exclude_manager(
            tmp_path / "e.config",
            {"path": {"rules": [{"contains_folder": ["marker"], "level": 3}]}},
        )

        # a folder's direct children are always attached, so level 3 needs
        # two further levels materialised
        assert FilterOptions.inspect_depth_for(exclude) == 2

    def test_no_contains_rule_means_no_extra_reading(self, tmp_path: Path):
        exclude = exclude_manager(tmp_path / "e.config", {"name": {"rules": [{"equals": ["x"]}]}})

        assert FilterOptions.inspect_depth_for(exclude) == 0

    def test_a_deeper_contains_rule_still_matches_after_pruning(self, workspace: Path, tmp_path: Path):
        make_tree(workspace, ["repo/.git/", "repo/one/two/marker/"])
        exclude = exclude_manager(
            tmp_path / "e.config",
            {"path": {"rules": [{"contains_folder": ["marker"], "level": 3}]}},
        )
        exclude.setup_rules([])
        opts = options(
            exclude=exclude,
            skip_names=[".git"],
            project_markers=[".git"],
            project_depth=1,
            inspect_depth=FilterOptions.inspect_depth_for(exclude),
        )

        crawled = crawl(workspace, opts)

        # the marker is three levels down and the project depth is 1, but the
        # rule declared level 3, so the crawler read far enough to match it
        assert "repo" not in folder_names(crawled)
