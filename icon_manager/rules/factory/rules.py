import logging
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterable, Sequence
from enum import Enum
from typing import Any, ClassVar, cast

from icon_manager.rules.base import FolderMatcher, Operator, Rule, RuleAttribute
from icon_manager.rules.mapping import rule_mapping
from icon_manager.rules.rules import (
    ChainedRule,
    ContainsFileRule,
    FolderRule,
)

log = logging.getLogger(__name__)


class ConfigKeys(str, Enum):
    ATTRIBUTE = "attribute"
    CONFIG = "config"
    ICON_FILE = "icon_file"
    COPY_ICON = "copy_icon"
    BEFORE_OR_AFTER = "before_or_after"
    OPERATOR = "operator"
    CASE_SENSITIVE = "case_sensitive"
    RULES = "rules"
    ORDER = "order"
    SEARCH_LEVEL = "level"
    ACTION = "action"


class ConfigValues(str, Enum):
    BEFORE_OR_AFTER = "before_or_after_values"


KNOWN_OPERATORS = (Operator.ANY, Operator.ALL)


def get_operator_enum(value: Any) -> Operator:
    """The operator ``value`` names, rejecting anything else.

    An unknown value used to come back as ``Operator.UNKNOWN``, which makes
    every rule using it return False - so a typo like ``"operator":
    "beides"`` produced a rule that looked configured and matched nothing,
    without a word.
    """
    if isinstance(value, Operator):
        return value
    if isinstance(value, str):
        for operator in KNOWN_OPERATORS:
            if operator.value == value.lower():
                return operator
    allowed = ", ".join(sorted(operator.value for operator in KNOWN_OPERATORS))
    # the same wording --check uses, so one mistake does not read as two
    raise ValueError(f"{value!r} is not an operator; use one of: {allowed}")


def get_operator(rule_config: dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    return get_operator_enum(rule_config.get(ConfigKeys.OPERATOR, default))


def pop_operator(rule_config: dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    return get_operator_enum(rule_config.pop(ConfigKeys.OPERATOR, default))


def get_rule_values(rule_config: dict[str, Any], rule: Rule) -> list[str]:
    """The values a rule matches against, as a list.

    A bare string is wrapped rather than used as-is: the rule iterates its
    values, so ``"equals": "docs"`` used to match folders called ``d``,
    ``o``, ``c`` and ``s`` and never ``docs``. ``--check`` reports it, and
    here it is read the way it was obviously meant.
    """
    values = rule_config.get(rule, [])
    if isinstance(values, str):
        return [values]
    if not isinstance(values, Iterable):
        raise ValueError(f'"{rule.value}" needs a list of values, got {values!r}')
    return list(values)


RULE_MAPPING = rule_mapping()


def get_rule_name(rule_config: dict[str, Any]) -> Rule:
    for rule in RULE_MAPPING.keys():
        name_value = rule_config.get(rule, None)
        if name_value is None:
            continue
        return rule
    return Rule.UNKNOWN


def get_rule_type(rule_config: dict[str, Any]) -> type[FolderMatcher] | None:
    rule = get_rule_name(rule_config)
    if rule == Rule.UNKNOWN:
        return None
    return RULE_MAPPING[rule]


class ARuleBuilder[TRule: FolderMatcher](ABC):
    """Builds one family of rules from the dicts in a config file.

    ``rule_type`` is the family's base class, used to check that the rule
    name in the config maps to a rule this builder may produce. It is a
    class attribute: it used to be pulled out of ``**kwargs`` in __init__
    and raise AttributeError when missing, which turned a constructor
    parameter into a runtime surprise.
    """

    rule_type: ClassVar[type[FolderMatcher]]

    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return []

    def is_builder(self, rule_config: dict[str, Any]) -> bool:
        return any(rule in rule_config.keys() for rule in self.__class__.builder_for_rules())

    def get_rule(self, rule_config: dict[str, Any]) -> Rule:
        rule_name = get_rule_name(rule_config)
        if rule_name == Rule.UNKNOWN:
            raise LookupError("Dict does NOT contain a known rule type")
        return rule_name

    def get_rule_type(self, rule_config: dict[str, Any]) -> type[TRule]:
        rule_type = get_rule_type(rule_config)
        if rule_type is None:
            raise RuntimeError(f"No rule type for config {rule_config}")
        if not issubclass(rule_type, self.rule_type):
            raise RuntimeError(f"{rule_type.__name__} is not a {self.rule_type.__name__}")
        # the issubclass check above is what makes this safe; a type checker
        # cannot narrow a class object to the type parameter from it
        return cast(type[TRule], rule_type)

    def get_case_sensitive(self, rule_config: dict[str, Any]) -> bool:
        return rule_config.pop(ConfigKeys.CASE_SENSITIVE, False)

    def can_build(self, rule_config: dict[str, Any]) -> bool:
        can_build = self.is_builder(rule_config)
        return can_build

    @abstractmethod
    def create(self, config: dict[str, Any], attribute: RuleAttribute) -> TRule:
        """Build the rule the config names, for the given folder attribute."""


class AAttributeRuleBuilder[TFolderRule: FolderRule](ARuleBuilder[TFolderRule]):
    def get_before_or_after_values(self, config: dict[str, Any]) -> Collection[str]:
        return config.get(ConfigValues.BEFORE_OR_AFTER, [])

    def add_before_or_after(self, config: dict[str, Any]) -> bool:
        return config.get(ConfigKeys.BEFORE_OR_AFTER, False)

    def create(self, config: dict[str, Any], attribute: RuleAttribute) -> TFolderRule:
        if attribute == RuleAttribute.UNKNOWN:
            raise ValueError(f"Unknown folder attribute for rule config {config}")
        return self.create_rule(attribute, config)

    @abstractmethod
    def create_rule(self, attribute: RuleAttribute, config: dict[str, Any]) -> TFolderRule: ...


class FolderRuleBuilder(AAttributeRuleBuilder[FolderRule]):
    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return [
            Rule.EQUALS,
            Rule.NOT_EQUALS,
            Rule.STARTS_WITH,
            Rule.ENDS_WITH,
            Rule.STARTS_OR_ENDS_WITH,
            Rule.CONTAINS,
            Rule.NOT_CONTAINS,
        ]

    rule_type: ClassVar[type[FolderMatcher]] = FolderRule

    def create_rule(self, attribute: RuleAttribute, config: dict[str, Any]) -> FolderRule:
        operator = pop_operator(config)
        case_sensitive = self.get_case_sensitive(config)
        rule = self.get_rule(config)
        values = get_rule_values(config, rule)
        before_or_after = self.add_before_or_after(config)
        before_or_after_values = self.get_before_or_after_values(config)
        rule_type = self.get_rule_type(config)
        return rule_type(
            attribute,
            operator,
            values,
            case_sensitive,
            before_or_after,
            before_or_after_values,
        )


class ContainsFileRuleBuilder(AAttributeRuleBuilder[ContainsFileRule]):
    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return [
            Rule.CONTAINS_FILE,
            Rule.NOT_CONTAINS_FILE,
            Rule.CONTAINS_FOLDER,
            Rule.NOT_CONTAINS_FOLDER,
        ]

    rule_type: ClassVar[type[FolderMatcher]] = ContainsFileRule

    def create_rule(self, attribute: RuleAttribute, config: dict[str, Any]) -> ContainsFileRule:
        rule = self.get_rule(config)
        values = get_rule_values(config, rule)
        operator = get_operator(config)
        case_sensitive = self.get_case_sensitive(config)
        before_or_after = self.add_before_or_after(config)
        before_or_after_values = self.get_before_or_after_values(config)
        level = config.pop(ConfigKeys.SEARCH_LEVEL, 1)
        rule_type = self.get_rule_type(config)
        return rule_type(
            attribute,
            operator,
            values,
            case_sensitive,
            before_or_after,
            before_or_after_values,
            level,
        )


SINGLE_BUILDER_TYPES: Iterable[type[AAttributeRuleBuilder]] = [
    FolderRuleBuilder,
    ContainsFileRuleBuilder,
]


def get_single_builders() -> Iterable[AAttributeRuleBuilder]:
    builders = []
    for builder_type in SINGLE_BUILDER_TYPES:
        builder = builder_type()
        builders.append(builder)
    return builders


def create_single_rule(
    rules: Iterable[AAttributeRuleBuilder], config: dict[str, Any], attribute: RuleAttribute
) -> FolderMatcher:
    for builder in rules:
        if not builder.can_build(config):
            continue
        return builder.create(config, attribute)
    raise RuntimeError("No single rule could be created")


class ChainedRuleBuilder(ARuleBuilder[ChainedRule]):
    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return [Rule.CHAINED]

    rule_type: ClassVar[type[FolderMatcher]] = ChainedRule

    def __init__(self) -> None:
        self.single_builders = get_single_builders()

    def get_rule_configs(self, rule_config: dict[str, Any]) -> Collection[dict[str, Any]]:
        rule = self.get_rule(rule_config)
        return rule_config.get(rule, [])

    def get_single_rules(self, rule_config: dict[str, Any], attribute: RuleAttribute) -> Sequence[FolderMatcher]:
        return [
            create_single_rule(self.single_builders, config, attribute) for config in self.get_rule_configs(rule_config)
        ]

    def create(self, config: dict[str, Any], attribute: RuleAttribute) -> ChainedRule:
        if attribute == RuleAttribute.UNKNOWN:
            raise ValueError(f"Unknown folder attribute for rule config {config}")
        operator = pop_operator(config)
        rule_type = self.get_rule_type(config)
        rules = self.get_single_rules(config, attribute)
        return rule_type(attribute, operator, rules)


BUILDER_TYPES: Iterable[type[ARuleBuilder]] = [
    FolderRuleBuilder,
    ContainsFileRuleBuilder,
    ChainedRuleBuilder,
]


def get_builders() -> Iterable[ARuleBuilder]:
    builders = []
    for builder_type in BUILDER_TYPES:
        builder = builder_type()
        builders.append(builder)
    return builders
