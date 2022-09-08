import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import (Any, Collection, Dict, Iterable, Optional, Sequence, Type,
                    TypeVar)

from icon_manager.interfaces.factory import ContentFactory
from icon_manager.rules.base import (IFilterRule, ISingleRule, Operator, Rule,
                                     RuleAttribute)
from icon_manager.rules.mapping import rule_mapping
from icon_manager.rules.rules import ChainedRule, ContainsFileRule, FolderRule

log = logging.getLogger(__name__)


class ConfigKeys(str, Enum):
    ATTRIBUTE = 'attribute'
    CONFIG = 'config'
    ICON_FILE = 'icon_file'
    BEFORE_OR_AFTER = 'before_or_after'
    OPERATOR = 'operator'
    CASE_SENSITIVE = 'case_sensitive'
    RULES = 'rules'
    ORDER = 'order'
    SEARCH_LEVEL = 'level'


class ConfigValues(str, Enum):
    BEFORE_OR_AFTER = 'before_or_after_values'


def get_operator_enum(value: str) -> Operator:
    value = value.lower()
    for operator in Operator:
        if operator.value != value:
            continue
        return operator
    return Operator.UNKNOWN


def get_operator(rule_config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = rule_config.get(ConfigKeys.OPERATOR, default)
    return get_operator_enum(value)


def pop_operator(rule_config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = rule_config.pop(ConfigKeys.OPERATOR, default)
    return get_operator_enum(value)


RULE_MAPPING = rule_mapping()


def get_rule_name(rule_config: Dict[str, Any]) -> Rule:
    for rule in RULE_MAPPING.keys():
        name_value = rule_config.get(rule, None)
        if name_value is None:
            continue
        return rule
    return Rule.UNKNOWN


def get_rule_type(rule_config: Dict[str, Any]) -> Optional[Type[IFilterRule]]:
    rule = get_rule_name(rule_config)
    if rule == Rule.UNKNOWN:
        return None
    return RULE_MAPPING[rule]


TRule = TypeVar('TRule', bound=IFilterRule)


class ARuleBuilder(ABC, ContentFactory[Dict[str, Any], TRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return []

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        rule_type = kwargs.get('rule_type', None)
        if rule_type is None:
            raise AttributeError('rule_type is not in kwargs')
        self.rule_type: Type[TRule] = rule_type

    def is_builder(self, rule_config: Dict[str, Any]) -> bool:
        return any(rule in rule_config.keys() for rule in self.__class__.builder_for_rules())

    def get_rule(self, rule_config: Dict[str, Any]) -> Rule:
        rule_name = get_rule_name(rule_config)
        if rule_name == Rule.UNKNOWN:
            raise LookupError('Dict does NOT contain a known rule type')
        return rule_name

    def get_rule_type(self, rule_config: Dict[str, Any]) -> Type[TRule]:
        rule_type = get_rule_type(rule_config)
        if rule_type is None or not issubclass(rule_type, self.rule_type):
            raise RuntimeError('No Filter rule type found')
        if not issubclass(rule_type, self.rule_type):
            raise RuntimeError(f'Rule is NOT of type {self.rule_type}')
        return rule_type

    def get_attribute(self, **kwargs) -> RuleAttribute:
        attribute = kwargs.get(ConfigKeys.ATTRIBUTE, RuleAttribute.UNKNOWN)
        if attribute == RuleAttribute.UNKNOWN:
            message = f'Key "{ConfigKeys.ATTRIBUTE}" does NOT exist in Dict'
            raise ValueError(message)
        return attribute

    def get_case_sensitive(self, rule_config: Dict[str, Any]) -> bool:
        return rule_config.pop(ConfigKeys.CASE_SENSITIVE, False)

    def can_build(self, rule_config: Dict[str, Any]) -> bool:
        can_build = self.is_builder(rule_config)
        return can_build

    @ abstractmethod
    def create(self, config: Dict[str, Any], **kwargs) -> TRule:
        ...


TFolderRule = TypeVar('TFolderRule', bound=FolderRule)


class ASingleRuleBuilder(ARuleBuilder[TFolderRule]):

    def get_before_or_after_values(self, config: Dict[str, Any]) -> Collection[str]:
        return config.get(ConfigValues.BEFORE_OR_AFTER, [])

    def add_before_or_after(self, config: Dict[str, Any]) -> bool:
        return config.get(ConfigKeys.BEFORE_OR_AFTER, False)

    def create(self, config: Dict[str, Any], **kwargs) -> TFolderRule:
        attribute: str = self.get_attribute(**kwargs)
        return self.create_rule(attribute, config)

    @ abstractmethod
    def create_rule(self, attribute: RuleAttribute, config: Dict[str, Any]) -> TFolderRule:
        ...


class FolderRuleBuilder(ASingleRuleBuilder[FolderRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[Rule]:
        return [Rule.EQUALS, Rule.NOT_EQUALS, Rule.STARTS_WITH, Rule.ENDS_WITH,
                Rule.STARTS_OR_ENDS_WITH, Rule.CONTAINS, Rule.NOT_CONTAINS]

    def __init__(self, **kwargs) -> None:
        super().__init__(rule_type=FolderRule, **kwargs)

    def create_rule(self, attribute: RuleAttribute, config: Dict[str, Any]) -> FolderRule:
        operator = pop_operator(config)
        case_sensitive = self.get_case_sensitive(config)
        rule = self.get_rule(config)
        values = config.get(rule, [])
        before_or_after = self.add_before_or_after(config)
        before_or_after_values = self.get_before_or_after_values(config)
        rule_type = self.get_rule_type(config)
        return rule_type(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values)


class ContainsFileRuleBuilder(ASingleRuleBuilder[ContainsFileRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return [Rule.CONTAINS_FILE]

    def __init__(self, **kwargs) -> None:
        super().__init__(rule_type=ContainsFileRule, **kwargs)

        # def can_build(self, rule_config: Dict[str, Any]) -> bool:
        #     if ConfigKeys.SEARCH_LEVEL not in rule_config:
        #         return False
        #     return True

    def create_rule(self, attribute: RuleAttribute, rule_config: Dict[str, Any]) -> ContainsFileRule:
        rule = self.get_rule(rule_config)
        values = rule_config.get(rule, [])
        operator = get_operator(rule_config)
        case_sensitive = self.get_case_sensitive(rule_config)
        before_or_after = self.add_before_or_after(rule_config)
        before_or_after_values = self.get_before_or_after_values(rule_config)
        level = rule_config.pop(ConfigKeys.SEARCH_LEVEL, 1)
        rule_type = self.get_rule_type(rule_config)
        return rule_type(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values, level)


SINGLE_BUILDER_TYPES: Iterable[Type[ASingleRuleBuilder]] = [
    FolderRuleBuilder,
    ContainsFileRuleBuilder
]


def get_single_builders() -> Iterable[ASingleRuleBuilder]:
    builders = []
    for builder_type in SINGLE_BUILDER_TYPES:
        builder = builder_type()
        builders.append(builder)
    return builders


def create_single_rule(rules: Iterable[ASingleRuleBuilder], config: Dict[str, Any], **kwargs) -> ISingleRule:
    for builder in rules:
        if not builder.can_build(config):
            continue
        return builder.create(config, **kwargs)
    raise RuntimeError(f'No single rule could be created')


class ChainedRuleBuilder(ARuleBuilder[ChainedRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return [Rule.CHAINED]

    def __init__(self, **kwargs) -> None:
        super().__init__(rule_type=ChainedRule, **kwargs)
        self.single_builders = get_single_builders()

    def get_rule_configs(self, rule_config: Dict[str, Any]) -> Collection[Dict[str, Any]]:
        rule = self.get_rule(rule_config)
        return rule_config.get(rule, [])

    # def can_build(self, rule_config: Dict[str, Any]) -> bool:
    #     if not super().can_build(rule_config):
    #         return False
    #     return len(self.get_rule_configs(rule_config)) > 0

    def get_single_rules(self, rule_config: Dict[str, Any], **kwargs) -> Sequence[FolderRule]:
        rules = []
        for config in self.get_rule_configs(rule_config):
            rule = create_single_rule(self.single_builders, config, **kwargs)
            rules.append(rule)
        return rules

    def create(self, config: Dict[str, Any], **kwargs) -> ChainedRule:
        operator = pop_operator(config)
        rule_type = self.get_rule_type(config)
        rules = self.get_single_rules(config, **kwargs)
        attribute: str = self.get_attribute(**kwargs)
        return rule_type(attribute, operator, rules)


BUILDER_TYPES: Iterable[Type[ARuleBuilder]] = [
    FolderRuleBuilder,
    ContainsFileRuleBuilder,
    ChainedRuleBuilder
]


def get_builders() -> Iterable[ARuleBuilder]:
    builders = []
    for builder_type in BUILDER_TYPES:
        builder = builder_type()
        builders.append(builder)
    return builders
