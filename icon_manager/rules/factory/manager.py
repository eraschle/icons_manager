import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from typing import Any

from icon_manager.data.base import Source
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.resource import exclude_rules_template_path
from icon_manager.interfaces.path import ConfigFile, JsonFile
from icon_manager.rules.base import FolderAction, FolderMatcher, Operator, RuleAttribute
from icon_manager.rules.factory.rules import (
    ConfigKeys,
    get_builders,
    pop_operator,
)
from icon_manager.rules.manager import (
    AttributeRuleHandler,
    ConfigRuleController,
    ExcludeManager,
    ExcludeRule,
    RuleManager,
)
from icon_manager.validation.problems import ConfigFileError

DEFAULT_ORDER = 5

log = logging.getLogger(__name__)


class AttributeCheckerFactory:
    """Builds the rules of one attribute section of a config file."""

    def __init__(self) -> None:
        self.builders = get_builders()

    def create_rule(self, rule_config: dict[str, Any], attribute: RuleAttribute) -> FolderMatcher:
        for builder in self.builders:
            if not builder.can_build(rule_config):
                continue
            return builder.create(rule_config, attribute)
        raise RuntimeError(f"No rule builder for config {rule_config}")

    def create_rules(self, config: dict[str, Any], attribute: RuleAttribute) -> Sequence[FolderMatcher]:
        return [self.create_rule(rule_config, attribute) for rule_config in config.get(ConfigKeys.RULES, [])]

    def create(self, config: dict[str, Any], attribute: RuleAttribute) -> AttributeRuleHandler:
        operator = pop_operator(config, Operator.ANY)
        rules = self.create_rules(config, attribute)
        return AttributeRuleHandler(attribute, operator, rules)


def get_rule_attribute(value) -> RuleAttribute:
    if not isinstance(value, str):
        return RuleAttribute.UNKNOWN
    for attr in RuleAttribute:
        if value.lower() != attr.value:
            continue
        return attr
    return RuleAttribute.UNKNOWN


class SourceCheckerBuilder:
    """Builds the whole rule set of one config file section."""

    def __init__(self) -> None:
        self.factory = AttributeCheckerFactory()

    def get_attribute_checkers(self, config: dict[str, Any]) -> Sequence[AttributeRuleHandler]:
        return [
            self.factory.create(rules_config, get_rule_attribute(attribute))
            for attribute, rules_config in config.items()
        ]

    def create(self, config: dict[str, Any]) -> ConfigRuleController:
        operator = pop_operator(config, Operator.ALL)
        return ConfigRuleController(self.get_attribute_checkers(config), operator)


class AManagerFactory[TModel, TContent: Iterable](ABC):
    """Reads a rule config file and builds the manager it describes."""

    def __init__(self, source: Source | None = None) -> None:
        self.source = source or JsonSource()
        self.builder = SourceCheckerBuilder()
        self._template: dict[str, Any] = {}

    def get_config_section(self, config: dict[str, Any]) -> TContent:
        section: TContent | None = config.get(ConfigKeys.CONFIG, None)
        if section is None:
            raise ValueError(f'Key "{ConfigKeys.CONFIG.value}" does not exist in the config file')
        return section

    def create(self, file: JsonFile) -> TModel:
        """Read ``file`` and build what it describes.

        Every failure below is re-raised naming the file. Without that the
        user got messages like ``No rule builder for config {'equal': ['x']}``
        with no way to tell which of their config files meant it.
        """
        content = self.source.read(file)
        try:
            return self.create_with_content(self.get_config_section(content), file)
        except ConfigFileError:
            raise
        except (ValueError, LookupError, RuntimeError, TypeError) as ex:
            raise ConfigFileError(file.path, str(ex)) from ex

    @abstractmethod
    def create_with_content(self, config: TContent, file: JsonFile) -> TModel:
        """Build the manager from the config section of ``file``."""


class RuleManagerFactory(AManagerFactory[RuleManager, dict[str, Any]]):
    def create_with_content(self, config: dict[str, Any], file: JsonFile) -> RuleManager:
        copy_icon = config.pop(ConfigKeys.COPY_ICON, None)
        order = get_order(config)
        return RuleManager(file, self.builder.create(config), order, copy_icon)

    def update(self, config: JsonFile, template_file: JsonFile) -> None:
        content = self.source.read(config)
        if len(self._template) == 0:
            self._template = self.source.read(template_file)
        updated = {}
        for section, values in self._template.items():
            updated[section] = values
            if section == ConfigKeys.CONFIG:
                updated[section] = content[section]
        self.source.write(config, updated)
        log.info(f"Updated config {config.name_wo_extension}")


def get_order(config: dict[str, Any], default: int = DEFAULT_ORDER) -> int:
    """The icon's priority, which has to be a whole number.

    A string got through before and only surfaced as
    ``'<' not supported between instances of 'int' and 'str'`` while sorting
    the library, naming no file.
    """
    value = config.pop(ConfigKeys.ORDER, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f'"{ConfigKeys.ORDER.value}" has to be a whole number, got {value!r}')
    return value


def get_folder_action(value: Any, default: FolderAction = FolderAction.SKIP) -> FolderAction:
    """Read a section's ``"action"`` key, rejecting anything unknown.

    ``search`` is not a valid exclude action: a section that asked for it
    would say "match this folder and then do what you would have done
    anyway", which is a typo, not an instruction.
    """
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"{value!r} is not an action; use one of: skip, leaf")
    for action in (FolderAction.SKIP, FolderAction.LEAF):
        if value.lower() == action.value:
            return action
    allowed = ", ".join(a.value for a in (FolderAction.SKIP, FolderAction.LEAF))
    raise ValueError(f"{value!r} is not an action; use one of: {allowed}")


class ExcludeManagerFactory(AManagerFactory[ExcludeManager, Iterable[dict[str, Any]]]):
    def create_with_content(self, config: Iterable[dict[str, Any]], file: JsonFile) -> ExcludeManager:
        return ExcludeManager([self.create_rule(section) for section in config])

    def create_rule(self, section: dict[str, Any]) -> ExcludeRule:
        action = get_folder_action(section.pop(ConfigKeys.ACTION, None))
        return ExcludeRule(self.builder.create(section), action)

    def copy_template(self, config: ConfigFile) -> None:
        template = ConfigFile(exclude_rules_template_path())
        template.copy_to(config)

    def prepare_template(self, config: ConfigFile) -> None:
        content = self.source.read(config)
        self.source.write(config, content)

    def create_template(self, config: ConfigFile) -> ConfigFile:
        self.copy_template(config)
        self.prepare_template(config)
        return config
