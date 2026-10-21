"""Fixtures for behaviour tests that run against a real directory tree.

These tests build an icon library and a folder tree under ``tmp_path`` and
let the real crawler, rule engine and desktop.ini writer work on them. Only
the Windows ``attrib`` calls do not take effect off Windows; they go through
``os.system``, fail silently there and change nothing the assertions look at.
"""

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from icon_manager.config.user import UserConfig
from icon_manager.interfaces.path import IconSearchFolder, JsonFile, SearchFolder
from icon_manager.library.controller import IconLibraryController
from icon_manager.rules.factory.manager import ExcludeManagerFactory, RuleManagerFactory
from icon_manager.rules.manager import ExcludeManager, RuleManager


def write_json(path: Path, content: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return path


def make_tree(root: Path, spec: Iterable[str]) -> Path:
    """Create the paths in ``spec`` under ``root``.

    An entry ending in ``/`` becomes a directory, anything else an empty file
    (its parent directories are created too), so a whole fixture tree reads as
    a list of paths.
    """
    for entry in spec:
        target = root / entry.rstrip("/")
        if entry.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
    return root


def icon_config(**attributes: Any) -> dict[str, Any]:
    """An icon configuration as it is stored next to an .ico file.

    Each keyword is a folder attribute ("name", "path", ...) mapped to that
    attribute's rule section, e.g. ``icon_config(name={"rules": [{"equals":
    ["docs"]}]})``.
    """
    config: dict[str, Any] = {"order": 5}
    config.update(attributes)
    return {"config": config}


def add_icon(library: Path, name: str, /, **attributes: Any) -> Path:
    """Put ``name``.ico plus its rule configuration into ``library``."""
    library.mkdir(parents=True, exist_ok=True)
    icon = library / f"{name}.ico"
    icon.write_bytes(b"\x00\x00\x01\x00")
    write_json(library / f"{name}.json", icon_config(**attributes))
    return icon


def rule_manager(library: Path, name: str, /, **attributes: Any) -> RuleManager:
    """A RuleManager built from a real config file, as production does."""
    add_icon(library, name, **attributes)
    return RuleManagerFactory().create(JsonFile(str(library / f"{name}.json")))


def exclude_manager(path: Path, *sections: Mapping[str, Any]) -> ExcludeManager:
    """An ExcludeManager built from a real exclude config file."""
    write_json(path, {"config": list(sections)})
    return ExcludeManagerFactory().create(JsonFile(str(path)))


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """The icon library folder: .ico files and their .json rule configs."""
    path = tmp_path / "library"
    path.mkdir()
    return path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """The folder tree that icons get applied to."""
    path = tmp_path / "workspace"
    path.mkdir()
    return path


@pytest.fixture
def user_config(library: Path, workspace: Path) -> UserConfig:
    return UserConfig(
        name="behaviour",
        icons_path=SearchFolder(str(library)),
        search_folders=[IconSearchFolder(str(workspace), copy_icon=False)],
        code_folders=[],
        exclude_folders=[],
        before_or_after=[],
        copy_icon=False,
    )


@pytest.fixture
def settings_controller(user_config: UserConfig) -> IconLibraryController:
    """A library controller that has read the library from disk."""
    from icon_manager.crawler.crawler import crawling_icons

    controller = IconLibraryController(user_config)
    content = crawling_icons(user_config.icons_path, IconLibraryController.icons_extensions)
    controller.create_settings(content)
    return controller
