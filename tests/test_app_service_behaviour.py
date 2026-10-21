"""The application service running every operation over two user configs.

IconsAppService is a fan-out: each operation applies to every user
configuration. These tests run the real operations against two real
libraries and folder trees, which is also what guards the fan-out against
the two configurations seeing each other's state again.
"""

from pathlib import Path

import pytest

from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.interfaces.path import IconSearchFolder, SearchFolder
from icon_manager.rules.manager import ExcludeManager
from icon_manager.services.app_service import IconsAppService
from tests.conftest import add_icon, make_tree


@pytest.fixture
def two_configs(tmp_path: Path) -> list[UserConfig]:
    configs = []
    for name, folder_name in (("alpha", "docs"), ("beta", "music")):
        library, space = tmp_path / f"lib_{name}", tmp_path / f"space_{name}"
        add_icon(library, name, name={"rules": [{"equals": [folder_name]}]})
        make_tree(space, [f"{folder_name}/", "untouched/"])
        configs.append(
            UserConfig(
                name=name,
                icons_path=SearchFolder(str(library)),
                search_folders=[IconSearchFolder(str(space), copy_icon=False)],
                code_folders=[],
                exclude_folders=[],
                before_or_after=[],
                copy_icon=False,
            )
        )
    return configs


@pytest.fixture
def service(two_configs: list[UserConfig]) -> IconsAppService:
    app_service = IconsAppService(AppConfig(two_configs, ExcludeManager([]), []))
    app_service.setup()
    app_service.create_settings()
    app_service.setup_and_merge_user_service()
    return app_service


def ini_files(config: UserConfig) -> set[str]:
    root = Path(config.search_folders[0].path)
    return {ini.parent.name for ini in root.rglob("desktop.ini")}


class TestApplyingAcrossConfigurations:
    def test_setup_creates_one_service_per_configuration(self, service: IconsAppService):
        assert [s.user_config.name for s in service.services] == ["alpha", "beta"]

    def test_each_configuration_applies_only_its_own_rules(
        self, service: IconsAppService, two_configs: list[UserConfig]
    ):
        service.find_and_apply_matches()

        alpha, beta = two_configs
        assert ini_files(alpha) == {"docs"}
        assert ini_files(beta) == {"music"}

    def test_delete_removes_the_icons_of_every_configuration(
        self, service: IconsAppService, two_configs: list[UserConfig]
    ):
        service.find_and_apply_matches()

        service.find_existing_content()
        service.delete_icon_settings()

        assert all(ini_files(config) == set() for config in two_configs)

    def test_re_apply_is_a_no_op_without_copied_icons(self, service: IconsAppService, two_configs: list[UserConfig]):
        service.find_and_apply_matches()
        service.find_existing_content()

        service.re_apply_matched_icons()

        # nothing was copied, so there is no __icon__ folder to restore from
        assert ini_files(two_configs[0]) == {"docs"}


class TestLibraryOperationsAcrossConfigurations:
    def test_create_library_configs_touches_every_library(
        self, service: IconsAppService, two_configs: list[UserConfig]
    ):
        for config in two_configs:
            (Path(config.icons_path.path) / "extra.ico").write_bytes(b"\x00\x00\x01\x00")
        service.create_settings()

        service.create_library_configs()

        assert all((Path(config.icons_path.path) / "extra.json").is_file() for config in two_configs)

    def test_update_library_configs_keeps_the_rules(self, service: IconsAppService, two_configs: list[UserConfig]):
        service.update_library_configs()

        service.find_and_apply_matches()
        assert ini_files(two_configs[0]) == {"docs"}

    def test_delete_library_configs_empties_every_library(
        self, service: IconsAppService, two_configs: list[UserConfig]
    ):
        service.delete_library_configs()

        for config in two_configs:
            assert list(Path(config.icons_path.path).glob("*.json")) == []

    def test_archive_moves_only_rule_less_icons(self, service: IconsAppService, two_configs: list[UserConfig]):
        library = Path(two_configs[0].icons_path.path)
        add_icon(library, "ruleless", name={"rules": []})
        service.create_settings()

        service.archive_icons_and_configs()

        assert not (library / "ruleless.ico").exists()
        assert (library / "alpha.ico").is_file()


class TestBeforeOrAfterIsMergedFromTheAppConfig:
    def test_the_app_wide_affixes_reach_the_rules(self, tmp_path: Path):
        library, space = tmp_path / "lib", tmp_path / "space"
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"], "before_or_after": True}]})
        make_tree(space, ["_docs/"])
        config = UserConfig(
            name="affixes",
            icons_path=SearchFolder(str(library)),
            search_folders=[IconSearchFolder(str(space), copy_icon=False)],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )
        service = IconsAppService(AppConfig([config], ExcludeManager([]), ["_"]))
        service.setup()
        service.create_settings()
        service.setup_and_merge_user_service()

        service.find_and_apply_matches()

        assert ini_files(config) == {"_docs"}
