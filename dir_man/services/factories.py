from typing import (Any, Collection, Dict, Generic, Iterable, Protocol, Type,
                    TypeVar)

from dir_man.models.config import IconConfig
from dir_man.models.container import IconContainer
from dir_man.models.path import IconFile
from dir_man.models.rules import (ContainsRule, EqualsRule, FolderRule,
                                  NotContainsRule, Operator)

TModel = TypeVar('TModel', covariant=True)


class Factory(Protocol, Generic[TModel]):
    def create(self, config: Dict[str, Any], **kwargs) -> TModel:
        ...


class RuleFactory(Factory[Collection[FolderRule]]):
    def __init__(self, rule_map: Dict[str, Type[FolderRule]]) -> None:
        self.rule_map = rule_map

    def get_name(self, rule_dict: Dict[str, Any]) -> str:
        for name in rule_dict.keys():
            return name
        raise ValueError('Rules dict has no entries')

    def get_rule(self, rule_dict: Dict[str, Any]) -> FolderRule:
        attribute = rule_dict.pop('attribute')
        operator = rule_dict.pop('operator', Operator.ANY)
        case_sensitive = rule_dict.pop('case_sensitive', False)
        # Only the name and values entry should exists
        rule_name = self.get_name(rule_dict)
        rule_type = self.rule_map.get(rule_name)
        if rule_type is None:
            raise NotImplementedError(f'No rule "{rule_name}" exists')
        values = rule_dict.get(rule_name, [])
        return rule_type(attribute, values, operator, case_sensitive)

    def get_rules(self, rules_dict: Iterable[Dict[str, Any]]) -> Collection[FolderRule]:
        rules = []
        for rule_dict in rules_dict:
            rule = self.get_rule(rule_dict)
            rules.append(rule)
        return rules

    def create(self, config: Dict[str, Any], **kwargs) -> Collection[FolderRule]:
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


RULE_MAP: Dict[str, Type[FolderRule]] = {
    'equals': EqualsRule,
    'contains': ContainsRule,
    'not_contains': NotContainsRule
}


class ConfigFactory(Factory[IconConfig]):

    def __init__(self, config: Dict[str, Any]) -> None:
        self.rule_factory = RuleFactory(RULE_MAP)
        icon_root_path = IconContainer(config.pop('icon_path'))
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
