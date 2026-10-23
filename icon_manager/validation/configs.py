"""Reads configuration files for problems instead of for rules.

Everything here walks the raw JSON and reports, rather than building and
raising. It uses the same vocabulary the factories use - ``rule_mapping()``,
``RuleAttribute``, ``Operator``, ``ConfigKeys`` - so the schema is not
written down twice: a rule the factory can build is a rule this accepts.

The point is to collect. A factory stops at the first thing it cannot do,
which is right when it is building something, and useless when you want to
know what is wrong with twenty config files.
"""

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from icon_manager.rules.base import RuleAttribute
from icon_manager.rules.factory.rules import KNOWN_OPERATORS, ConfigKeys, ConfigValues
from icon_manager.rules.mapping import rule_mapping
from icon_manager.validation.problems import ConfigProblem, Severity

RULE_NAMES = frozenset(rule.value for rule in rule_mapping())
ATTRIBUTE_NAMES = frozenset(attr.value for attr in RuleAttribute if attr is not RuleAttribute.UNKNOWN)
OPERATOR_NAMES = frozenset(operator.value for operator in KNOWN_OPERATORS)

SECTION_OPTIONS = frozenset(
    {
        ConfigKeys.OPERATOR.value,
        ConfigKeys.ACTION.value,
        ConfigKeys.ORDER.value,
        ConfigKeys.COPY_ICON.value,
        ConfigKeys.ICON_FILE.value,
    }
)
"""Keys a config section may carry besides the rule sections themselves."""

RULE_OPTIONS = frozenset(
    {
        ConfigKeys.OPERATOR.value,
        ConfigKeys.CASE_SENSITIVE.value,
        ConfigKeys.BEFORE_OR_AFTER.value,
        ConfigKeys.SEARCH_LEVEL.value,
        ConfigValues.BEFORE_OR_AFTER.value,
    }
)
"""Keys a single rule may carry besides the rule name itself."""


def _problem(file: Path, location: str, message: str, severity: Severity) -> ConfigProblem:
    return ConfigProblem(file=file.name, location=location, message=message, severity=severity)


def _error(file: Path, location: str, message: str) -> ConfigProblem:
    return _problem(file, location, message, Severity.ERROR)


def _warning(file: Path, location: str, message: str) -> ConfigProblem:
    return _problem(file, location, message, Severity.WARNING)


def read_json(file: Path) -> tuple[dict[str, Any] | None, list[ConfigProblem]]:
    """Parse ``file``, reporting rather than raising if it cannot be read."""
    try:
        content = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        return None, [_error(file, f"line {ex.lineno}", f"not valid JSON: {ex.msg}")]
    except OSError as ex:
        return None, [_error(file, "", f"cannot be read: {ex.strerror}")]
    if not isinstance(content, dict):
        return None, [_error(file, "", f"the top level has to be an object, not {type(content).__name__}")]
    return content, []


def _check_operator(file: Path, where: str, holder: dict[str, Any]) -> Iterator[ConfigProblem]:
    if ConfigKeys.OPERATOR.value not in holder:
        return
    value = holder[ConfigKeys.OPERATOR.value]
    if isinstance(value, str) and value.lower() in OPERATOR_NAMES:
        return
    allowed = ", ".join(sorted(OPERATOR_NAMES))
    yield _error(
        file,
        f"{where}.{ConfigKeys.OPERATOR.value}",
        # an unknown operator used to leave the rule matching nothing at all
        f"{value!r} is not an operator; use one of: {allowed}",
    )


def _check_rule(file: Path, where: str, rule: Any) -> Iterator[ConfigProblem]:
    if not isinstance(rule, dict):
        yield _error(file, where, f"a rule has to be an object, not {type(rule).__name__}")
        return

    named = sorted(set(rule) & RULE_NAMES)
    if not named:
        unknown = sorted(set(rule) - RULE_OPTIONS)
        hint = f"; did you mean one of: {', '.join(sorted(RULE_NAMES))}" if unknown else ""
        yield _error(file, where, f"no known rule name among {sorted(rule)}{hint}")
        return
    if len(named) > 1:
        yield _error(file, where, f"more than one rule name in the same object: {named}")
        return

    name = named[0]
    values = rule[name]
    yield from _check_operator(file, where, rule)

    if name == "chained":
        if not isinstance(values, list):
            yield _error(file, f"{where}.{name}", "chained takes a list of rules")
            return
        if not values:
            yield _warning(file, f"{where}.{name}", "chained has no rules, so it matches nothing")
        for index, nested in enumerate(values):
            yield from _check_rule(file, f"{where}.{name}[{index}]", nested)
        return

    if isinstance(values, str):
        yield _warning(
            file,
            f"{where}.{name}",
            # the rule iterates its values, so a bare string used to be read
            # character by character: "docs" matched d, o, c and s
            f'{values!r} is a single value; write ["{values}"] so it is not read as one value per letter',
        )
    elif not isinstance(values, list):
        yield _error(file, f"{where}.{name}", f"needs a list of values, got {type(values).__name__}")
    elif not values:
        yield _warning(file, f"{where}.{name}", "has no values, so this rule matches nothing")

    level = rule.get(ConfigKeys.SEARCH_LEVEL.value)
    if level is not None:
        if isinstance(level, bool) or not isinstance(level, int):
            yield _error(file, f"{where}.{ConfigKeys.SEARCH_LEVEL.value}", f"has to be a number, got {level!r}")
        elif level < 1:
            yield _error(file, f"{where}.{ConfigKeys.SEARCH_LEVEL.value}", f"has to be at least 1, got {level}")
        elif not name.endswith(("_file", "_folder")):
            yield _warning(
                file,
                f"{where}.{ConfigKeys.SEARCH_LEVEL.value}",
                f"has no effect on {name}; only contains_file and contains_folder look below a folder",
            )


def _check_attribute_section(file: Path, where: str, section: Any) -> Iterator[ConfigProblem]:
    if not isinstance(section, dict):
        yield _error(file, where, f"has to be an object with a {ConfigKeys.RULES.value!r} list")
        return
    yield from _check_operator(file, where, section)

    if ConfigKeys.RULES.value not in section:
        yield _warning(file, where, f"has no {ConfigKeys.RULES.value!r}, so it matches nothing")
        return
    rules = section[ConfigKeys.RULES.value]
    if not isinstance(rules, list):
        yield _error(file, f"{where}.{ConfigKeys.RULES.value}", "has to be a list")
        return
    if not rules:
        yield _warning(file, f"{where}.{ConfigKeys.RULES.value}", "is empty, so it matches nothing")
    for index, rule in enumerate(rules):
        yield from _check_rule(file, f"{where}.{ConfigKeys.RULES.value}[{index}]", rule)


def _check_rule_sections(file: Path, where: str, sections: dict[str, Any]) -> Iterator[ConfigProblem]:
    """The ``name`` / ``path`` / ``parent_*`` sections shared by both formats."""
    for key, section in sections.items():
        if key in SECTION_OPTIONS:
            continue
        if key not in ATTRIBUTE_NAMES:
            allowed = ", ".join(sorted(ATTRIBUTE_NAMES))
            yield _error(file, f"{where}.{key}", f"is not a folder attribute; use one of: {allowed}")
            continue
        yield from _check_attribute_section(file, f"{where}.{key}", section)


def validate_icon_config(file: Path) -> list[ConfigProblem]:
    """Check one ``name.json`` beside a ``name.ico``."""
    content, problems = read_json(file)
    if content is None:
        return problems

    section = content.get(ConfigKeys.CONFIG.value)
    if section is None:
        return [*problems, _error(file, "", f"has no {ConfigKeys.CONFIG.value!r} section")]
    if not isinstance(section, dict):
        return [*problems, _error(file, ConfigKeys.CONFIG.value, "has to be an object")]

    order = section.get(ConfigKeys.ORDER.value)
    if order is not None and (isinstance(order, bool) or not isinstance(order, int)):
        problems.append(
            _error(
                file,
                f"{ConfigKeys.CONFIG.value}.{ConfigKeys.ORDER.value}",
                # a string here only surfaced while sorting the library, as a
                # TypeError that named no file
                f"has to be a whole number, got {order!r}",
            )
        )
    copy_icon = section.get(ConfigKeys.COPY_ICON.value)
    if copy_icon is not None and not isinstance(copy_icon, bool):
        problems.append(
            _error(
                file,
                f"{ConfigKeys.CONFIG.value}.{ConfigKeys.COPY_ICON.value}",
                f"has to be true or false, got {copy_icon!r}",
            )
        )

    rule_keys = {key for key in section if key in ATTRIBUTE_NAMES}
    if not rule_keys:
        problems.append(_warning(file, ConfigKeys.CONFIG.value, "has no rule section, so this icon is never applied"))
    problems.extend(_check_rule_sections(file, ConfigKeys.CONFIG.value, section))
    return problems


def validate_exclude_config(file: Path) -> list[ConfigProblem]:
    """Check an ``excluded_rules.config``."""
    content, problems = read_json(file)
    if content is None:
        return problems

    sections = content.get(ConfigKeys.CONFIG.value)
    if sections is None:
        return [*problems, _error(file, "", f"has no {ConfigKeys.CONFIG.value!r} section")]
    if not isinstance(sections, list):
        return [*problems, _error(file, ConfigKeys.CONFIG.value, "has to be a list of rule sections")]

    for index, section in enumerate(sections):
        where = f"{ConfigKeys.CONFIG.value}[{index}]"
        if not isinstance(section, dict):
            problems.append(_error(file, where, f"has to be an object, not {type(section).__name__}"))
            continue
        action = section.get(ConfigKeys.ACTION.value)
        if action is not None and (not isinstance(action, str) or action.lower() not in ("skip", "leaf")):
            problems.append(
                _error(file, f"{where}.{ConfigKeys.ACTION.value}", f"{action!r} is not an action; use skip or leaf")
            )
        if action is None:
            problems.append(
                _warning(
                    file,
                    where,
                    f"has no {ConfigKeys.ACTION.value!r}, so it defaults to skip: no icon and no search below",
                )
            )
        problems.extend(_check_rule_sections(file, where, section))
    return problems


def validate_library(library: Path) -> list[ConfigProblem]:
    """Check an icon library folder for icons and configs without a partner.

    Both used to be dropped in silence, so an icon that was never applied
    looked exactly like one whose rules simply did not match.
    """
    if not library.is_dir():
        return [ConfigProblem(library.name, "", "the icon library does not exist", Severity.ERROR)]

    problems: list[ConfigProblem] = []
    icons = {path.stem for path in library.glob("*.ico")}
    configs = {path.stem for path in library.glob("*.json")}
    for name in sorted(icons - configs):
        problems.append(
            ConfigProblem(f"{name}.ico", "", "has no .json beside it, so it is never applied", Severity.WARNING)
        )
    for name in sorted(configs - icons):
        problems.append(ConfigProblem(f"{name}.json", "", "has no .ico beside it, so it is ignored", Severity.WARNING))
    for name in sorted(icons & configs):
        problems.extend(validate_icon_config(library / f"{name}.json"))
    return problems


def validate_user_config(file: Path) -> list[ConfigProblem]:
    """Check one user ``*.config``."""
    content, problems = read_json(file)
    if content is None:
        return problems

    section = content.get(ConfigKeys.CONFIG.value)
    if not isinstance(section, dict):
        return [*problems, _error(file, "", f"has no {ConfigKeys.CONFIG.value!r} object")]

    if not section.get("icons_path"):
        problems.append(_error(file, f"{ConfigKeys.CONFIG.value}.icons_path", "is missing; it names the icon library"))

    folders = section.get("search_folders")
    if not folders:
        problems.append(
            _error(file, f"{ConfigKeys.CONFIG.value}.search_folders", "is missing or empty; nothing would be searched")
        )
    elif not isinstance(folders, list):
        problems.append(_error(file, f"{ConfigKeys.CONFIG.value}.search_folders", "has to be a list of objects"))
    else:
        for index, folder in enumerate(folders):
            where = f"{ConfigKeys.CONFIG.value}.search_folders[{index}]"
            if not isinstance(folder, dict):
                problems.append(_error(file, where, f"has to be an object with a 'path', not {type(folder).__name__}"))
            elif not folder.get("path"):
                problems.append(_error(file, f"{where}.path", "is missing"))

    depth = section.get("project_depth")
    if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int)):
        problems.append(
            _error(file, f"{ConfigKeys.CONFIG.value}.project_depth", f"has to be a whole number, got {depth!r}")
        )
    elif isinstance(depth, int) and depth < 0:
        problems.append(_error(file, f"{ConfigKeys.CONFIG.value}.project_depth", f"cannot be negative, got {depth}"))

    for key in ("code_folders", "exclude_folders", "before_or_after"):
        value = section.get(key)
        if value is not None and not isinstance(value, list):
            problems.append(
                _error(file, f"{ConfigKeys.CONFIG.value}.{key}", f"has to be a list, got {type(value).__name__}")
            )
    return problems


def validate_config_folder(folder: Path, exclude_name: str, app_name: str) -> list[ConfigProblem]:
    """Check every configuration file in the folder the app reads from."""
    if not folder.is_dir():
        return [ConfigProblem(str(folder), "", "the configuration folder does not exist", Severity.ERROR)]

    problems: list[ConfigProblem] = []
    for file in sorted(folder.glob("*.config")):
        if file.name == app_name:
            continue
        if file.name == exclude_name:
            problems.extend(validate_exclude_config(file))
        else:
            problems.extend(validate_user_config(file))
    return problems


def libraries_of(folder: Path, exclude_name: str, app_name: str) -> Iterable[Path]:
    """The icon libraries the user configs in ``folder`` point at."""
    found: list[Path] = []
    for file in sorted(folder.glob("*.config")):
        if file.name in (app_name, exclude_name):
            continue
        content, _ = read_json(file)
        section = (content or {}).get(ConfigKeys.CONFIG.value)
        if not isinstance(section, dict):
            continue
        icons_path = section.get("icons_path")
        if isinstance(icons_path, str) and icons_path:
            found.append(Path(icons_path))
    return found
