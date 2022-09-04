from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Collection, Dict, Iterable, Optional, Type, TypeVar

from icon_manager.interfaces.factory import ContentFactory
from icon_manager.rules.base import IconRule, Operator
from icon_manager.rules.rules import ChainedRule, ContainsFileRule, FolderRule


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


class Attributes(str, Enum):
    ATTR_NAME = 'name'
    ATTR_PATH = 'path'


def get_operator_enum(value: str) -> Operator:
    value = value.lower()
    for operator in Operator:
        if operator != value:
            continue
        return operator
    return Operator.UNKNOWN


def get_operator(rule_config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = rule_config.get(ConfigKeys.OPERATOR, default)
    return get_operator_enum(value)


def pop_operator(rule_config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = rule_config.pop(ConfigKeys.OPERATOR, default)
    return get_operator_enum(value)


TRule = TypeVar('TRule', bound=IconRule)


def get_rule_name(rule_mapping: Dict[str, Type[IconRule]], rule_config: Dict[str, Any]) -> Optional[str]:
    for name in rule_mapping.keys():
        name_value = rule_config.get(name, None)
        if name_value is None:
            continue
        return name
    return None


def get_rule_type(rule_mapping: Dict[str, Type[IconRule]], rule_config: Dict[str, Any]) -> Optional[Type[IconRule]]:
    rule_name = get_rule_name(rule_mapping, rule_config)
    if rule_name is None:
        return None
    return rule_mapping[rule_name]


class IconRuleBuilder(ABC, ContentFactory[Dict[str, Any], TRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return []

    def __init__(self, rule_type: Type[TRule], **kwargs) -> None:
        super().__init__(**kwargs)
        rule_mapping = kwargs.get('rule_mapping', None)
        if rule_mapping is None:
            raise AttributeError('rule_mapping is not in kwargs')
        self.rule_mapping = rule_mapping
        self.rule_type = rule_type

    def is_builder(self, rule_config: Dict[str, Any]) -> bool:
        return any(rule in rule_config.keys() for rule in self.__class__.builder_for_rules())

    def get_rule_name(self, rule_config: Dict[str, Any]) -> str:
        rule_name = get_rule_name(self.rule_mapping, rule_config)
        if rule_name is None:
            raise LookupError('Dict does NOT contain a known rule type')
        return rule_name

    def get_rule_type(self, rule_config: Dict[str, Any]) -> Type[TRule]:
        rule_type = get_rule_type(self.rule_mapping, rule_config)
        if rule_type is None or not issubclass(rule_type, self.rule_type):
            raise RuntimeError('No Filter rule type found')
        if not issubclass(rule_type, self.rule_type):
            raise RuntimeError(f'Rule is NOT of type {self.rule_type}')
        return rule_type

    def get_attribute(self, **kwargs) -> str:
        attribute: str = kwargs.get(ConfigKeys.ATTRIBUTE, None)
        if attribute is None:
            message = f'Key "{ConfigKeys.ATTRIBUTE}" does NOT exist in Dict'
            raise ValueError(message)
        return attribute

    def get_case_sensitive(self, rule_config: Dict[str, Any]) -> bool:
        return rule_config.pop(ConfigKeys.CASE_SENSITIVE, False)

    def can_build(self, rule_config: Dict[str, Any]) -> bool:
        can_build = self.is_builder(rule_config)
        return can_build

    @ abstractmethod
    def create(self, rule_config: Dict[str, Any], **kwargs) -> TRule:
        ...


TFolderRule = TypeVar('TFolderRule', bound=FolderRule)


class BaseFolderRuleBuilder(IconRuleBuilder[TFolderRule]):

    def __init__(self, rule_type: Type[TFolderRule], **kwargs) -> None:
        super().__init__(rule_type, **kwargs)

    def get_before_or_after_values(self, rule_config: Dict[str, Any]) -> Collection[str]:
        return rule_config.get(ConfigValues.BEFORE_OR_AFTER, [])

    def add_before_or_after(self, rule_config: Dict[str, Any]) -> bool:
        return rule_config.get(ConfigKeys.BEFORE_OR_AFTER, False)

    def create(self, rule_config: Dict[str, Any], **kwargs) -> TFolderRule:
        attribute: str = self.get_attribute(**kwargs)
        return self.create_rule(attribute, rule_config)

    @ abstractmethod
    def create_rule(self, attribute: str, rule_config: Dict[str, Any]) -> TFolderRule:
        ...


class FolderRuleBuilder(BaseFolderRuleBuilder[FolderRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return ['equals', 'not_equals', 'starts_with', 'ends_with',
                'start_or_ends_with', 'contains', 'not_contains', 'chained']

    def __init__(self, **kwargs) -> None:
        super().__init__(FolderRule, **kwargs)

        # def can_build(self, rule_config: Dict[str, Any]) -> bool:
        #     rule_name = get_rule_name(self.rule_mapping, rule_config)
        #     if any(key in rule_config for key in NOT_DEFAULT_CONFIG):
        #         return False
        #     if rule_name is None:
        #         return False
        #     try:
        #         self.get_rule_type(rule_config)
        #         return True
        #     except:
        #         return False

    def create_rule(self, attribute: str, rule_config: Dict[str, Any]) -> FolderRule:
        operator = pop_operator(rule_config)
        case_sensitive = self.get_case_sensitive(rule_config)
        rule_name = self.get_rule_name(rule_config)
        values = rule_config.get(rule_name, [])
        before_or_after = self.add_before_or_after(rule_config)
        before_or_after_values = self.get_before_or_after_values(rule_config)
        rule_type = self.get_rule_type(rule_config)
        return rule_type(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values)


class ContainsFileRuleBuilder(BaseFolderRuleBuilder[ContainsFileRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return ['contains_files']

    def __init__(self, **kwargs) -> None:
        super().__init__(ContainsFileRule, **kwargs)

        # def can_build(self, rule_config: Dict[str, Any]) -> bool:
        #     if ConfigKeys.SEARCH_LEVEL not in rule_config:
        #         return False
        #     return True

    def create_rule(self, attribute: str, rule_config: Dict[str, Any]) -> ContainsFileRule:
        rule_name = self.get_rule_name(rule_config)
        values = rule_config.get(rule_name, [])
        if attribute != Attributes.ATTR_PATH:
            message = f'Contains extension rules can only applied on {Attributes.ATTR_PATH} attribute'
            raise ValueError(message)
        operator = get_operator(rule_config)
        case_sensitive = self.get_case_sensitive(rule_config)
        before_or_after = self.add_before_or_after(rule_config)
        before_or_after_values = self.get_before_or_after_values(rule_config)
        level = rule_config.pop(ConfigKeys.SEARCH_LEVEL, 1)
        rule_type = self.get_rule_type(rule_config)
        return rule_type(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values, level)


class ChainedRuleBuilder(IconRuleBuilder[ChainedRule]):

    @classmethod
    def builder_for_rules(cls) -> Iterable[str]:
        return ['chained']

    def __init__(self, **kwargs) -> None:
        super().__init__(ChainedRule, **kwargs)
        create_rule_func = kwargs.get('create_rule_func', None)
        if create_rule_func is None:
            raise AttributeError('create_rule_func is not in kwargs')
        if not callable(create_rule_func):
            raise AttributeError('create_rule_func is not callable functions')
        self.create_rule_func = create_rule_func

    def get_rule_configs(self, rule_config: Dict[str, Any]) -> Collection[Dict[str, Any]]:
        rule_name = self.get_rule_name(rule_config)
        return rule_config.get(rule_name, [])

    # def can_build(self, rule_config: Dict[str, Any]) -> bool:
    #     if not super().can_build(rule_config):
    #         return False
    #     return len(self.get_rule_configs(rule_config)) > 0

    def get_chained_rules(self, rule_config: Dict[str, Any], **kwargs) -> Collection[FolderRule]:
        rules = []
        for config in self.get_rule_configs(rule_config):
            rule = self.create_rule_func(config, **kwargs)
            rules.append(rule)
        return rules

    def create(self, rule_config: Dict[str, Any], **kwargs) -> ChainedRule:
        operator = pop_operator(rule_config)
        rule_type = self.get_rule_type(rule_config)
        folder_rules = self.get_chained_rules(rule_config, **kwargs)
        attribute: str = self.get_attribute(**kwargs)
        return rule_type(attribute, operator, folder_rules)
