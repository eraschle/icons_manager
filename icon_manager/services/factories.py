from typing import (Any, Collection, Dict, Generic, Iterable, List, Protocol,
                    Type, TypeVar)

from icon_manager.models.config import IconConfig
from icon_manager.models.rules import (ChainedRules, ContainsExtensionRule,
                                       FilterRule, FilterRuleManager,
                                       FolderRule, Operator)

TModel = TypeVar('TModel', covariant=True)


class Factory(Protocol, Generic[TModel]):
    def create(self, config: Dict[str, Any], **kwargs) -> TModel:
        ...


ATTRIBUTE_KEY: str = 'attribute'
CONFIG_KEY: str = 'config'
ICON_FILE_KEY: str = 'icon_file'
ATTR_NAME_KEY: str = 'name'
ATTR_PATH_KEY: str = 'path'
OPERATOR_KEY: str = 'operator'
CASE_SENSITIVE_KEY: str = 'case_sensitive'
RULES_KEY: str = 'rules'
ORDER_KEY: str = 'order'
LEVEL_KEY: str = 'level'


def get_operator_enum(value: str) -> Operator:
    value = value.lower()
    for operator in Operator:
        if operator != value:
            continue
        return operator
    return Operator.UNKNOWN


def get_operator(config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = config.get(OPERATOR_KEY, default)
    return get_operator_enum(value)


def pop_operator(config: Dict[str, Any], default: Operator = Operator.ANY) -> Operator:
    value = config.pop(OPERATOR_KEY, default)
    return get_operator_enum(value)


class FilterRuleFactory(Factory[Collection[FilterRule]]):

    def __init__(self, rule_mapping: Dict[str, Type[FilterRule]]) -> None:
        self.rule_mapping = rule_mapping

    def get_rule_name(self, rule_dict: Dict[str, Any]) -> str:
        for name in self.rule_mapping.keys():
            name_value = rule_dict.get(name, None)
            if name_value is None:
                continue
            return name
        raise LookupError('Dict does NOT contain a known rule type')

    def get_rule_type(self, rule_dict: Dict[str, Any]) -> Type[FilterRule]:
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.rule_mapping.get(rule_name, None)
        if rule_type is None:
            raise LookupError('Dict does NOT contain a known rule type')
        return rule_type

    def is_chained_rule(self, rule_dict: Dict[str, Any]) -> bool:
        rule_type = self.get_rule_type(rule_dict)
        if rule_type is None or not issubclass(rule_type, ChainedRules):
            return False
        return True

    def create_filter_rule(self, attribute: str, rule_dict: Dict[str, Any]) -> FolderRule:
        operator = pop_operator(rule_dict)
        case_sensitive = rule_dict.pop(CASE_SENSITIVE_KEY, False)
        # Only the name and values entry should exists
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.get_rule_type(rule_dict)
        if not issubclass(rule_type, FolderRule):
            raise KeyError(f'Method only creates "{FolderRule}"')
        values = rule_dict.get(rule_name, [])
        if issubclass(rule_type, ContainsExtensionRule):
            if attribute != ATTR_PATH_KEY:
                message = f'Contains extension rules can only applied on {ATTR_PATH_KEY} attribute'
                raise ValueError(message)
            level = rule_dict.pop(LEVEL_KEY, 1)
            return rule_type(attribute, values, operator, case_sensitive, level)
        return rule_type(attribute, values, operator, case_sensitive)

    def get_chained_rules(self, attribute: str, rules_dict: Iterable[Dict[str, Any]]) -> Iterable[FolderRule]:
        filter_rules = []
        for rule_dict in rules_dict:
            folder_rule = self.create_filter_rule(attribute, rule_dict)
            filter_rules.append(folder_rule)
        return filter_rules

    def create_chained_rules(self, attribute: str, rule_dict: Dict[str, Any]) -> FilterRule:
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.get_rule_type(rule_dict)
        if not issubclass(rule_type, ChainedRules):
            raise KeyError(f'Method only creates "{ChainedRules}"')
        rules_dict = rule_dict.get(rule_name, [])
        rules = self.get_chained_rules(attribute, rules_dict)
        operator = pop_operator(rule_dict)
        return rule_type(rules, operator)

    def get_rule(self, attribute: str, rule_dict: Dict[str, Any]) -> FilterRule:
        if self.is_chained_rule(rule_dict):
            return self.create_chained_rules(attribute, rule_dict)
        return self.create_filter_rule(attribute, rule_dict)

    def get_rules(self, attribute: str, rules_dict: Iterable[Dict[str, Any]]) -> Collection[FilterRule]:
        rules = []
        for rule_dict in rules_dict:
            rule = self.get_rule(attribute, rule_dict)
            rules.append(rule)
        return rules

    def create(self, config: Dict[str, Any], **kwargs) -> Collection[FilterRule]:
        attribute: str = kwargs.get(ATTRIBUTE_KEY, None)
        if attribute is None:
            message = f'Key "{ATTRIBUTE_KEY}" does NOT exist in Dict'
            raise ValueError(message)
        rules: Iterable[Dict[str, Any]] = config.get(RULES_KEY, [])
        return self.get_rules(attribute, rules)


class RuleManagerFactory(Factory[FilterRuleManager]):

    def __init__(self, rule_mapping: Dict[str, Type[FilterRule]]) -> None:
        self.rule_factory = FilterRuleFactory(rule_mapping)

    def create(self, config: Dict[str, Any], **kwargs) -> FilterRuleManager:
        attribute: str = kwargs.get(ATTRIBUTE_KEY, None)
        if attribute is None:
            message = f'Key "{ATTRIBUTE_KEY}" does NOT exist in Dict'
            raise ValueError(message)
        self.attribute = attribute
        operator = get_operator(config)
        rules = self.rule_factory.create(config, **kwargs)
        return FilterRuleManager(attribute, rules, operator)


class ConfigFactory(Factory[IconConfig]):

    def __init__(self, rule_mapping: Dict[str, Type[FilterRule]], copy_icon: bool) -> None:
        self.manager_factory = RuleManagerFactory(rule_mapping)
        self.copy_icon = copy_icon

    def create(self, config: Dict[str, Any], **kwargs) -> IconConfig:
        icon_file = kwargs.get(ICON_FILE_KEY, None)
        if icon_file is None:
            message = f'Argument "{ICON_FILE_KEY}" does NOT exist'
            raise ValueError(message)
        config = config.get(CONFIG_KEY, None)
        if config is None:
            message = f'Key "{CONFIG_KEY}" does NOT exist in Dict'
            raise ValueError(message)
        order = config.pop(ORDER_KEY, 5)
        managers: List[FilterRuleManager] = []
        for attribute, rules_dict in config.items():
            manager = self.manager_factory.create(config=rules_dict,
                                                  attribute=attribute)
            if manager.is_empty():
                continue
            managers.append(manager)
        return IconConfig(icon_file, managers, self. copy_icon, order)
