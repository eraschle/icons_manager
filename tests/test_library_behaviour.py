"""Managing the icon library itself: configs, updates, archiving.

The library is a folder of ``name.ico`` files, each with a ``name.json``
beside it holding the rules for that icon. These tests operate on a real
library folder.
"""

import json
from pathlib import Path

from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.crawler.crawler import crawling_icons
from icon_manager.interfaces.path import SearchFolder
from icon_manager.library.controller import IconLibraryController
from icon_manager.library.models import ArchiveFolder, IconFile
from icon_manager.rules.manager import ExcludeManager
from icon_manager.services.app_service import IconsAppService
from tests.conftest import add_icon


def read_library(user_config: UserConfig) -> IconLibraryController:
    controller = IconLibraryController(user_config)
    controller.create_settings(crawling_icons(user_config.icons_path, IconLibraryController.icons_extensions))
    return controller


class TestCreatingConfigsForNewIcons:
    def test_an_icon_without_a_config_gets_one_from_the_template(self, user_config: UserConfig, library: Path):
        (library / "fresh.ico").write_bytes(b"\x00\x00\x01\x00")

        read_library(user_config).create_icon_configs()

        config = library / "fresh.json"
        assert config.is_file()
        assert "config" in json.loads(config.read_text(encoding="utf-8"))

    def test_an_existing_config_is_not_overwritten(self, user_config: UserConfig, library: Path):
        add_icon(library, "mine", name={"rules": [{"equals": ["keep"]}]})
        before = (library / "mine.json").read_text(encoding="utf-8")

        read_library(user_config).create_icon_configs()

        assert (library / "mine.json").read_text(encoding="utf-8") == before


class TestUpdatingConfigs:
    def test_the_rules_survive_an_update_while_the_documentation_is_refreshed(
        self, user_config: UserConfig, library: Path
    ):
        add_icon(library, "mine", name={"rules": [{"equals": ["target"]}]})

        read_library(user_config).update_icon_configs()

        content = json.loads((library / "mine.json").read_text(encoding="utf-8"))
        assert content["config"]["name"]["rules"] == [{"equals": ["target"]}]
        # the template's reference sections come back
        assert "rules" in content


class TestDeletingConfigs:
    def test_the_configs_go_and_the_icons_stay(self, user_config: UserConfig, library: Path):
        add_icon(library, "one", name={"rules": [{"equals": ["a"]}]})
        add_icon(library, "two", name={"rules": [{"equals": ["b"]}]})

        read_library(user_config).delete_icon_configs()

        assert not (library / "one.json").exists()
        assert not (library / "two.json").exists()
        assert (library / "one.ico").is_file()
        assert (library / "two.ico").is_file()


class TestArchiving:
    def test_an_icon_whose_config_has_no_rules_is_moved_to_the_archive(self, user_config: UserConfig, library: Path):
        add_icon(library, "unused", name={"rules": []})
        add_icon(library, "used", name={"rules": [{"equals": ["target"]}]})

        read_library(user_config).archive_library()

        archive = library / ArchiveFolder.folder_name
        assert (archive / "unused.ico").is_file()
        assert (archive / "unused.json").is_file()
        assert not (library / "unused.ico").exists()
        assert (library / "used.ico").is_file(), "an icon with rules must stay"

    def test_archived_icons_are_not_read_back_as_settings(self, user_config: UserConfig, library: Path):
        add_icon(library, "unused", name={"rules": []})
        read_library(user_config).archive_library()

        settings = read_library(user_config).settings(clean_empty=False)

        assert [setting.name for setting in settings] == []


class TestFindingASettingByItsIcon:
    def test_matches_on_the_icon_file_name(self, user_config: UserConfig, library: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        controller = read_library(user_config)

        found = controller.setting_by_icon(IconFile(str(library / "docs.ico")))

        assert found is not None
        assert found.name == "docs"

    def test_returns_none_for_an_unknown_icon(self, user_config: UserConfig, library: Path):
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        controller = read_library(user_config)

        assert controller.setting_by_icon(IconFile(str(library / "nope.ico"))) is None


class TestOneFailingConfigurationDoesNotStopTheOthers:
    def test_the_remaining_configurations_still_run(self, tmp_path: Path, caplog):
        broken = UserConfig(
            name="broken",
            icons_path=SearchFolder(str(tmp_path / "missing_library")),
            search_folders=[],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )
        library = tmp_path / "good_library"
        add_icon(library, "docs", name={"rules": [{"equals": ["docs"]}]})
        good = UserConfig(
            name="good",
            icons_path=SearchFolder(str(library)),
            search_folders=[],
            code_folders=[],
            exclude_folders=[],
            before_or_after=[],
            copy_icon=False,
        )
        service = IconsAppService(AppConfig([broken, good], ExcludeManager([]), []))
        service.setup()

        service.create_settings()

        assert "Exception" in caplog.text, "the failure must be reported"
        good_service = next(s for s in service.services if s.user_config is good)
        assert [setting.name for setting in good_service.settings.settings()] == ["docs"]
