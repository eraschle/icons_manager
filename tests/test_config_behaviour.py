"""Reading the configuration files that drive the tool.

The config format is the other half of the user-facing contract, so these
tests write real .config files and read them back through the factories.
"""

import json
import os
from pathlib import Path

import pytest

from icon_manager.config.app import AppConfigFactory
from icon_manager.config.user import UserConfigFactory
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers import resource
from icon_manager.helpers.environment import get_converted_env_path
from icon_manager.interfaces.path import ConfigFile
from icon_manager.rules.factory.manager import ExcludeManagerFactory
from tests.conftest import write_json


def user_config_file(path: Path, **config) -> ConfigFile:
    write_json(path, {"config": config})
    return ConfigFile(str(path))


class TestReadingAUserConfig:
    def test_reads_every_section(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(library),
            search_folders=[{"path": str(workspace), "copy_icon": True}],
            code_folders=[".git"],
            exclude_folders=["obj"],
            before_or_after=["_", "-"],
            copy_icon=True,
        )

        config = UserConfigFactory(JsonSource()).create(file)

        assert config.icons_path.path == str(library)
        assert [folder.path for folder in config.search_folders] == [str(workspace)]
        assert config.search_folders[0].copy_icon is True
        assert list(config.code_folders) == [".git"]
        assert list(config.exclude_folders) == ["obj"]
        assert config.before_or_after == {"_", "-"}
        assert config.copy_icon is True

    def test_project_depth_defaults_to_one(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config", icons_path=str(library), search_folders=[{"path": str(workspace)}]
        )

        config = UserConfigFactory(JsonSource()).create(file)

        assert config.project_depth == 1

    def test_project_depth_is_read_from_the_file(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(library),
            search_folders=[{"path": str(workspace)}],
            project_depth=0,
        )

        config = UserConfigFactory(JsonSource()).create(file)

        assert config.project_depth == 0

    def test_the_skipped_names_are_both_lists(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(library),
            search_folders=[{"path": str(workspace)}],
            code_folders=[".git"],
            exclude_folders=["obj"],
        )

        config = UserConfigFactory(JsonSource()).create(file)

        # a marker folder gets no icon either, so both lists are skipped
        assert config.skip_folder_names == frozenset({".git", "obj"})

    def test_a_search_folder_that_does_not_exist_is_skipped(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(library),
            search_folders=[{"path": str(workspace)}, {"path": str(tmp_path / "gone")}],
        )

        config = UserConfigFactory(JsonSource()).create(file)

        assert [folder.path for folder in config.search_folders] == [str(workspace)]

    def test_a_missing_icons_path_is_rejected(self, tmp_path: Path, workspace: Path):
        file = user_config_file(tmp_path / "me.config", search_folders=[{"path": str(workspace)}])

        with pytest.raises(ValueError, match="Icon path"):
            UserConfigFactory(JsonSource()).create(file)

    def test_a_missing_search_folders_key_is_rejected(self, tmp_path: Path, library: Path):
        file = user_config_file(tmp_path / "me.config", icons_path=str(library))

        with pytest.raises(ValueError, match="Search folders"):
            UserConfigFactory(JsonSource()).create(file)

    def test_an_environment_variable_in_a_path_is_expanded(
        self, tmp_path: Path, library: Path, workspace: Path, monkeypatch
    ):
        monkeypatch.setenv("ICONS_TEST_ROOT", str(workspace.parent))
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(library),
            search_folders=[{"path": f"%ICONS_TEST_ROOT%{os.sep}{workspace.name}"}],
        )

        config = UserConfigFactory(JsonSource()).create(file)

        assert [folder.path for folder in config.search_folders] == [str(workspace)]

    def test_validate_rejects_a_library_that_is_gone(self, tmp_path: Path, workspace: Path):
        file = user_config_file(
            tmp_path / "me.config",
            icons_path=str(tmp_path / "no_library"),
            search_folders=[{"path": str(workspace)}],
        )
        config = UserConfigFactory(JsonSource()).create(file)

        with pytest.raises(ValueError, match="does not exist"):
            config.validate()


class TestEnvironmentPaths:
    def test_an_unset_variable_is_left_as_is(self):
        value = "%DEFINITELY_NOT_SET_12345%/sub"

        assert get_converted_env_path(value) == value

    def test_a_path_without_a_variable_is_unchanged(self):
        assert get_converted_env_path("/plain/path") == "/plain/path"


class TestReadingTheAppConfig:
    def test_collects_every_user_config_in_the_folder(self, tmp_path: Path, library: Path, workspace: Path):
        config_folder = tmp_path / "configs"
        for name in ("first", "second"):
            user_config_file(
                config_folder / f"{name}.config",
                icons_path=str(library),
                search_folders=[{"path": str(workspace)}],
            )
        app_file = write_json(
            config_folder / AppConfigFactory.APP_CONFIG_NAME,
            {"user_configs": str(config_folder), "before_or_after": ["_"]},
        )

        factory = AppConfigFactory(JsonSource(), ExcludeManagerFactory(JsonSource()))
        config = factory.create(ConfigFile(str(app_file)))

        assert sorted(user.name for user in config.user_configs) == ["first.config", "second.config"]
        assert list(config.before_or_after) == ["_"]

    def test_the_app_and_exclude_files_are_not_read_as_user_configs(
        self, tmp_path: Path, library: Path, workspace: Path
    ):
        config_folder = tmp_path / "configs"
        user_config_file(
            config_folder / "mine.config", icons_path=str(library), search_folders=[{"path": str(workspace)}]
        )
        write_json(config_folder / AppConfigFactory.EXCLUDE_NAME, {"config": []})
        app_file = write_json(config_folder / AppConfigFactory.APP_CONFIG_NAME, {"user_configs": str(config_folder)})

        factory = AppConfigFactory(JsonSource(), ExcludeManagerFactory(JsonSource()))
        config = factory.create(ConfigFile(str(app_file)))

        assert [user.name for user in config.user_configs] == ["mine.config"]

    def test_the_exclude_rules_are_copied_per_user_config(self, tmp_path: Path, library: Path, workspace: Path):
        config_folder = tmp_path / "configs"
        user_config_file(
            config_folder / "mine.config", icons_path=str(library), search_folders=[{"path": str(workspace)}]
        )
        write_json(
            config_folder / AppConfigFactory.EXCLUDE_NAME,
            {"config": [{"name": {"rules": [{"equals": ["skip"]}]}}]},
        )
        app_file = write_json(config_folder / AppConfigFactory.APP_CONFIG_NAME, {"user_configs": str(config_folder)})
        factory = AppConfigFactory(JsonSource(), ExcludeManagerFactory(JsonSource()))
        config = factory.create(ConfigFile(str(app_file)))

        first, second = config.create_exclude_rules(), config.create_exclude_rules()

        # each user config prepares its own copy with its own affixes
        assert first is not second
        assert first.rules[0] is not second.rules[0]

    def test_a_folder_without_any_user_config_is_rejected(self, tmp_path: Path):
        config_folder = tmp_path / "empty"
        config_folder.mkdir()
        app_file = write_json(config_folder / AppConfigFactory.APP_CONFIG_NAME, {"user_configs": str(config_folder)})
        factory = AppConfigFactory(JsonSource(), ExcludeManagerFactory(JsonSource()))

        # the interactive fallback asks the user; without a terminal it fails
        with pytest.raises((ValueError, OSError, EOFError)):
            factory.create(ConfigFile(str(app_file)))


class TestBundledResources:
    """Every template the tool copies must actually ship with it.

    The exclude-rules constant named a .config file while the resource is a
    .json, so creating that template raised FileNotFoundError. The mocked
    test for it patched the locator away and never touched the filesystem.
    """

    @pytest.mark.parametrize(
        "locator",
        [
            resource.icon_setting_template_path,
            resource.exclude_rules_template_path,
            resource.user_config_template_path,
            resource.app_config_template_path,
        ],
        ids=lambda fn: fn.__name__,
    )
    def test_the_template_exists_and_is_valid_json(self, locator):
        path = Path(locator())

        assert path.is_file(), f"missing resource: {path}"
        assert json.loads(path.read_text(encoding="utf-8"))
