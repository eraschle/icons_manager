"""What --check reports, and that the dangerous cases are no longer silent.

Six things used to go wrong without a word, or with a message that named no
file. Each of them has a test here: three are now refused while building,
three are reported as warnings, and every message says which file and which
key it came from.
"""

from pathlib import Path

import pytest

from icon_manager.interfaces.path import JsonFile
from icon_manager.rules.factory.manager import RuleManagerFactory
from icon_manager.validation.configs import (
    validate_exclude_config,
    validate_icon_config,
    validate_library,
    validate_user_config,
)
from icon_manager.validation.problems import (
    ConfigFileError,
    Severity,
    has_errors,
    problem_report,
)
from tests.conftest import add_icon, write_json


def icon_config(tmp_path: Path, **section) -> Path:
    return write_json(tmp_path / "icon.json", {"config": section})


def user_config(tmp_path: Path, **section) -> Path:
    return write_json(tmp_path / "me.config", {"config": section})


def messages(problems) -> str:
    return problem_report(problems)


def at(problems, location: str):
    """The problems reported for one key."""
    return [problem for problem in problems if problem.location == location]


class TestTheRuleEngineRefusesWhatUsedToBeSilent:
    """Three cases where a config looked fine and did the wrong thing."""

    def test_a_bare_string_is_read_as_one_value_not_one_per_letter(self, library: Path, tmp_path: Path):
        from tests.conftest import rule_manager

        manager = rule_manager(library, "icon", name={"rules": [{"equals": "docs"}]})
        manager.setup_rules([])

        from icon_manager.interfaces.path import Folder

        assert manager.is_allowed(Folder.from_path(str(tmp_path / "docs"), None)) is True
        for letter in "docs":
            assert manager.is_allowed(Folder.from_path(str(tmp_path / letter), None)) is False

    def test_an_unknown_operator_is_refused(self, library: Path):
        # it used to leave Operator.UNKNOWN behind, which makes every rule
        # return False: configured-looking and matching nothing
        add_icon(library, "icon", name={"rules": [{"equals": ["x"], "operator": "beides"}]})

        with pytest.raises(ConfigFileError, match="not an operator"):
            RuleManagerFactory().create(JsonFile(str(library / "icon.json")))

    def test_a_non_numeric_order_is_refused(self, library: Path):
        # it used to surface much later, while sorting the library, as
        # "'<' not supported between instances of 'int' and 'str'"
        add_icon(library, "icon", name={"rules": [{"equals": ["x"]}]})
        config = library / "icon.json"
        config.write_text(config.read_text().replace('"order": 5', '"order": "five"'), encoding="utf-8")

        with pytest.raises(ConfigFileError, match="whole number"):
            RuleManagerFactory().create(JsonFile(str(config)))


class TestEveryFailureNamesItsFile:
    @pytest.mark.parametrize(
        "section",
        [
            {"name": {"rules": [{"equal": ["typo"]}]}},
            {"nmae": {"rules": [{"equals": ["x"]}]}},
            {"name": {"rules": [{"equals": ["x"], "operator": "nonsense"}]}},
        ],
        ids=["unknown-rule", "unknown-attribute", "unknown-operator"],
    )
    def test_the_message_contains_the_file_name(self, library: Path, section):
        add_icon(library, "culprit", **section)

        with pytest.raises(ConfigFileError) as caught:
            RuleManagerFactory().create(JsonFile(str(library / "culprit.json")))

        assert "culprit.json" in str(caught.value)


class TestCheckingAnIconConfig:
    def test_a_sound_config_has_nothing_to_report(self, tmp_path: Path):
        file = icon_config(tmp_path, order=5, name={"rules": [{"equals": ["docs"]}]})

        assert validate_icon_config(file) == []

    def test_a_bare_string_value_is_a_warning(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": "docs"}]})

        found = at(validate_icon_config(file), "config.name.rules[0].equals")

        assert len(found) == 1
        assert found[0].severity is Severity.WARNING
        assert '["docs"]' in found[0].message

    def test_an_unknown_operator_is_an_error(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": ["x"], "operator": "beides"}]})

        found = at(validate_icon_config(file), "config.name.rules[0].operator")

        assert [problem.severity for problem in found] == [Severity.ERROR]

    def test_an_unknown_rule_name_lists_the_known_ones(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equal": ["x"]}]})

        found = at(validate_icon_config(file), "config.name.rules[0]")

        assert found and "equals" in found[0].message

    def test_an_unknown_attribute_lists_the_known_ones(self, tmp_path: Path):
        file = icon_config(tmp_path, nmae={"rules": [{"equals": ["x"]}]})

        found = at(validate_icon_config(file), "config.nmae")

        assert found and "parent_name" in found[0].message

    def test_order_and_copy_icon_are_not_read_as_rule_sections(self, tmp_path: Path):
        file = icon_config(tmp_path, order=1, copy_icon=True, name={"rules": [{"equals": ["x"]}]})

        assert validate_icon_config(file) == []

    def test_a_non_numeric_order_is_an_error(self, tmp_path: Path):
        file = icon_config(tmp_path, order="five", name={"rules": [{"equals": ["x"]}]})

        assert [p.severity for p in at(validate_icon_config(file), "config.order")] == [Severity.ERROR]

    def test_an_empty_value_list_is_a_warning(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": []}]})

        found = at(validate_icon_config(file), "config.name.rules[0].equals")

        assert [problem.severity for problem in found] == [Severity.WARNING]

    def test_a_config_without_any_rule_section_is_a_warning(self, tmp_path: Path):
        file = icon_config(tmp_path, order=5)

        assert [problem.severity for problem in at(validate_icon_config(file), "config")] == [Severity.WARNING]

    def test_a_level_on_a_rule_that_ignores_it_is_a_warning(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": ["x"], "level": 3}]})

        found = at(validate_icon_config(file), "config.name.rules[0].level")

        assert found and "contains_file" in found[0].message

    def test_a_level_on_contains_folder_is_fine(self, tmp_path: Path):
        file = icon_config(tmp_path, path={"rules": [{"contains_folder": ["src"], "level": 3}]})

        assert validate_icon_config(file) == []

    def test_chained_rules_are_checked_too(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"chained": [{"equals": ["a"]}, {"equal": ["b"]}]}]})

        found = at(validate_icon_config(file), "config.name.rules[0].chained[1]")

        assert [problem.severity for problem in found] == [Severity.ERROR]

    def test_broken_json_is_reported_not_raised(self, tmp_path: Path):
        file = tmp_path / "icon.json"
        file.write_text('{"config": {', encoding="utf-8")

        problems = validate_icon_config(file)

        assert has_errors(problems)
        assert "not valid JSON" in messages(problems)

    def test_a_missing_config_section_is_an_error(self, tmp_path: Path):
        file = write_json(tmp_path / "icon.json", {"rules": {}})

        assert has_errors(validate_icon_config(file))


class TestCheckingAnExcludeConfig:
    def test_a_sound_config_reports_only_the_implicit_default(self, tmp_path: Path):
        file = write_json(
            tmp_path / "excluded_rules.config",
            {"config": [{"action": "skip", "name": {"rules": [{"equals": ["x"]}]}}]},
        )

        assert validate_exclude_config(file) == []

    def test_a_missing_action_is_a_warning_naming_the_default(self, tmp_path: Path):
        file = write_json(tmp_path / "excluded_rules.config", {"config": [{"name": {"rules": [{"equals": ["x"]}]}}]})

        found = at(validate_exclude_config(file), "config[0]")

        assert [problem.severity for problem in found] == [Severity.WARNING]
        assert "skip" in found[0].message

    def test_an_unknown_action_is_an_error(self, tmp_path: Path):
        file = write_json(
            tmp_path / "excluded_rules.config",
            {"config": [{"action": "nonsense", "name": {"rules": []}}]},
        )

        assert has_errors(at(validate_exclude_config(file), "config[0].action"))

    def test_the_section_index_is_in_the_location(self, tmp_path: Path):
        file = write_json(
            tmp_path / "excluded_rules.config",
            {
                "config": [
                    {"action": "skip", "name": {"rules": [{"equals": ["ok"]}]}},
                    {"action": "skip", "name": {"rules": [{"equal": ["typo"]}]}},
                ]
            },
        )

        assert at(validate_exclude_config(file), "config[1].name.rules[0]")

    def test_a_config_that_is_not_a_list_is_an_error(self, tmp_path: Path):
        file = write_json(tmp_path / "excluded_rules.config", {"config": {"name": {}}})

        assert has_errors(validate_exclude_config(file))


class TestCheckingAUserConfig:
    def test_a_sound_config_has_nothing_to_report(self, tmp_path: Path, library: Path, workspace: Path):
        file = user_config(
            tmp_path,
            icons_path=str(library),
            search_folders=[{"path": str(workspace)}],
            project_depth=1,
        )

        assert validate_user_config(file) == []

    @pytest.mark.parametrize(
        ("section", "location"),
        [
            ({"search_folders": [{"path": "/x"}]}, "config.icons_path"),
            ({"icons_path": "/lib"}, "config.search_folders"),
            ({"icons_path": "/lib", "search_folders": [{"copy_icon": True}]}, "config.search_folders[0].path"),
            (
                {"icons_path": "/lib", "search_folders": [{"path": "/x"}], "project_depth": "one"},
                "config.project_depth",
            ),
            ({"icons_path": "/lib", "search_folders": [{"path": "/x"}], "project_depth": -1}, "config.project_depth"),
            ({"icons_path": "/lib", "search_folders": [{"path": "/x"}], "code_folders": ".git"}, "config.code_folders"),
        ],
        ids=[
            "no-library",
            "no-search-folders",
            "folder-without-path",
            "depth-not-a-number",
            "negative-depth",
            "list-as-string",
        ],
    )
    def test_each_mistake_is_reported_at_its_key(self, tmp_path: Path, section, location: str):
        file = user_config(tmp_path, **section)

        assert has_errors(at(validate_user_config(file), location))


class TestCheckingTheLibrary:
    def test_an_icon_without_a_config_is_a_warning(self, library: Path):
        (library / "orphan.ico").write_bytes(b"\x00")

        problems = validate_library(library)

        assert [problem.file for problem in problems] == ["orphan.ico"]
        assert problems[0].severity is Severity.WARNING
        assert "never applied" in problems[0].message

    def test_a_config_without_an_icon_is_a_warning(self, library: Path):
        write_json(library / "orphan.json", {"config": {"name": {"rules": [{"equals": ["x"]}]}}})

        problems = validate_library(library)

        assert [problem.file for problem in problems] == ["orphan.json"]
        assert problems[0].severity is Severity.WARNING

    def test_a_matched_pair_is_checked_as_an_icon_config(self, library: Path):
        add_icon(library, "icon", name={"rules": [{"equals": "docs"}]})

        problems = validate_library(library)

        assert at(problems, "config.name.rules[0].equals")

    def test_a_sound_library_has_nothing_to_report(self, library: Path):
        add_icon(library, "icon", name={"rules": [{"equals": ["docs"]}]})

        assert validate_library(library) == []

    def test_a_missing_library_is_an_error(self, tmp_path: Path):
        assert has_errors(validate_library(tmp_path / "gone"))


class TestTheReport:
    def test_errors_come_before_warnings(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": "string"}, {"equals": ["x"], "operator": "nope"}]})

        report = messages(validate_icon_config(file))

        assert report.index("ERROR") < report.index("WARNING")

    def test_every_line_names_the_file_and_the_key(self, tmp_path: Path):
        file = icon_config(tmp_path, order="five", name={"rules": [{"equals": "docs"}]})

        for line in messages(validate_icon_config(file)).splitlines():
            assert "icon.json" in line
            assert "[config." in line

    def test_has_errors_is_false_for_warnings_only(self, tmp_path: Path):
        file = icon_config(tmp_path, name={"rules": [{"equals": "docs"}]})

        problems = validate_icon_config(file)

        assert problems and not has_errors(problems)


class TestTheCommittedConfigsPassTheCheck:
    """The repository's own configuration files, run through --check."""

    REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

    def test_the_exclude_rules_have_no_errors(self):
        path = self.REPOSITORY_ROOT / "excluded_rules.config"
        if not path.is_file():
            pytest.skip("excluded_rules.config is not in this checkout")

        problems = validate_exclude_config(path)

        assert not has_errors(problems), messages(problems)

    @pytest.mark.parametrize("name", ["holdrio.config", "rsrg.config"])
    def test_a_user_config_has_no_errors(self, name: str):
        path = self.REPOSITORY_ROOT / name
        if not path.is_file():
            pytest.skip(f"{name} is not in this checkout")

        problems = validate_user_config(path)

        assert not has_errors(problems), messages(problems)

    def test_the_bundled_icon_template_has_no_errors(self):
        from icon_manager.helpers.resource import icon_setting_template_path

        problems = validate_icon_config(Path(icon_setting_template_path()))

        assert not has_errors(problems), messages(problems)
