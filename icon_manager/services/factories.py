from typing import (Any, Collection, Dict, Generic, Iterable, Protocol, Type,
                    TypeVar)

from icon_manager.config.config import ConfigManager
from icon_manager.models.config import IconConfig
from icon_manager.models.container import IconContainer
from icon_manager.models.path import IconFile
from icon_manager.models.rules import (ChainedRules, FilterRule, FolderRule,
                                       Operator)

TModel = TypeVar('TModel', covariant=True)


class Factory(Protocol, Generic[TModel]):
    def create(self, config: Dict[str, Any], **kwargs) -> TModel:
        ...


ATTRIBUTE_KEY: str = 'attribute'
OPERATOR_KEY: str = 'operator'
CASE_SENSITIVE_KEY: str = 'case_sensitive'


class RuleFactory(Factory[Collection[FilterRule]]):

    def __init__(self, rule_map: Dict[str, Type[FilterRule]]) -> None:
        self.rule_map = rule_map

    def get_rule_name(self, rule_dict: Dict[str, Any]) -> str:
        for name in self.rule_map.keys():
            name_value = rule_dict.get(name, None)
            if name_value is None:
                continue
            return name
        raise LookupError('Dict does NOT contain a known rule type')

    def get_rule_type(self, rule_dict: Dict[str, Any]) -> Type[FilterRule]:
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.rule_map.get(rule_name, None)
        if rule_type is None:
            raise LookupError('Dict does NOT contain a known rule type')
        return rule_type

    def is_chained_rule(self, rule_dict: Dict[str, Any]) -> bool:
        rule_type = self.get_rule_type(rule_dict)
        if rule_type is None or not issubclass(rule_type, ChainedRules):
            return False
        return True

    def create_folder_rule(self, rule_dict: Dict[str, Any]) -> FolderRule:
        attribute = rule_dict.pop(ATTRIBUTE_KEY)
        operator = rule_dict.pop(OPERATOR_KEY, Operator.ANY)
        case_sensitive = rule_dict.pop(CASE_SENSITIVE_KEY, False)
        # Only the name and values entry should exists
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.get_rule_type(rule_dict)
        if rule_type is None:
            raise NotImplementedError(f'No rule "{rule_name}" exists')
        if not issubclass(rule_type, FolderRule):
            raise KeyError(f'Method only creates "{FolderRule}"')
        values = rule_dict.get(rule_name, [])
        return rule_type(attribute, values, operator, case_sensitive)

    def get_chained_rules(self, rules_dict: Iterable[Dict[str, Any]], parent_dict: Dict[str, Any]) -> Iterable[FolderRule]:
        folder_rules = []
        for rule_dict in rules_dict:
            attr_value = rule_dict.get(ATTRIBUTE_KEY, None)
            if attr_value is None:
                rule_dict[ATTRIBUTE_KEY] = parent_dict.get(ATTRIBUTE_KEY)
            folder_rule = self.create_folder_rule(rule_dict)
            folder_rules.append(folder_rule)
        return folder_rules

    def get_rule_attributes(self, rule_dict: Dict[str, Any]) -> Dict[str, Any]:
        return {
            ATTRIBUTE_KEY: rule_dict.get(ATTRIBUTE_KEY),
            OPERATOR_KEY: rule_dict.get(OPERATOR_KEY, Operator.ANY),
            CASE_SENSITIVE_KEY: rule_dict.get(CASE_SENSITIVE_KEY, False)
        }

    def create_chained_rules(self, rule_dict: Dict[str, Any]) -> FilterRule:
        rule_name = self.get_rule_name(rule_dict)
        rule_type = self.get_rule_type(rule_dict)
        if not issubclass(rule_type, ChainedRules):
            raise KeyError(f'Method only creates "{ChainedRules}"')
        rule_attr = self.get_rule_attributes(rule_dict)
        rules_dict = rule_dict.get(rule_name, [])
        rules = self.get_chained_rules(rules_dict, rule_attr)
        operator = rule_dict.pop('operator', Operator.ANY)
        return rule_type(rules, operator)

    def get_rule(self, rule_dict: Dict[str, Any]) -> FilterRule:
        if self.is_chained_rule(rule_dict):
            return self.create_chained_rules(rule_dict)
        return self.create_folder_rule(rule_dict)

    def get_rules(self, rules_dict: Iterable[Dict[str, Any]]) -> Collection[FilterRule]:
        rules = []
        for rule_dict in rules_dict:
            rule = self.get_rule(rule_dict)
            rules.append(rule)
        return rules

    def create(self, config: Dict[str, Any], **kwargs) -> Collection[FilterRule]:
        rules: Iterable[Dict[str, Any]] = config.get('rules', [])
        return self.get_rules(rules)


class IconFactory(Factory[IconFile]):

    def __init__(self, root_path: IconContainer) -> None:
        self.icon_map = self.__get_map(root_path)

    def __get_map(self, root_path: IconContainer) -> Dict[str, IconFile]:
        icon_map = {}
        for icon in root_path.get_content():
            icon_name = icon.name_wo_extension
            icon_map[icon_name.lower()] = icon
        return icon_map

    def by_name(self, icon_name: str) -> IconFile:
        icon_name = icon_name.lower()
        icon = self.icon_map.get(icon_name, None)
        if icon is None:
            raise LookupError(f'No icon with name "{icon_name}" found')
        return icon

    def create(self, config: Dict[str, Any], **kwargs) -> IconFile:
        icon_name = config.get('icon', 'NO_ICON')
        return self.by_name(icon_name)


class ConfigFactory(Factory[IconConfig]):

    def __init__(self, config: ConfigManager) -> None:
        self.rule_factory = RuleFactory(config.rule_mapping())
        icon_root_path = IconContainer(config.icons_path())
        self.icon_factory = IconFactory(icon_root_path)

    def create(self, config: Dict[str, Any], **kwargs) -> IconConfig:
        icon = self.icon_factory.create(config)
        rules = self.rule_factory.create(config)
        apply_to_root = config.get('apply_to_root', True)
        order = config.get('order', 5)
        name = kwargs.get('name')
        if not isinstance(name, str):
            raise AttributeError(f'Expected str but got {type(name)}')
        return IconConfig(name, icon, rules, apply_to_root, order)
