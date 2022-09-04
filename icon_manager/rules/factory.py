import logging
from typing import Any, Dict, Iterable, List, Type

from icon_manager.data.json_source import JsonSource
from icon_manager.interfaces.factory import ContentFactory, FileFactory
from icon_manager.interfaces.path import JsonFile, PathModel
from icon_manager.rules.base import IconRule, Operator
from icon_manager.rules.builder import (BaseFolderRuleBuilder,
                                        ChainedRuleBuilder, ConfigKeys,
                                        ContainsFileRuleBuilder,
                                        FolderRuleBuilder, get_operator,
                                        pop_operator)
from icon_manager.rules.config import RuleConfig, RulesManager

log = logging.getLogger(__name__)

BUILDER_TYPES: Iterable[Type[BaseFolderRuleBuilder]] = [
    FolderRuleBuilder,
    ContainsFileRuleBuilder
]


def folder_builders(rule_mapping: Dict[str, Type[IconRule]]) -> Iterable[FolderRuleBuilder]:
    builders = []
    for builder_type in BUILDER_TYPES:
        builder = builder_type(rule_mapping=rule_mapping)
        builders.append(builder)
    return builders


class IconRuleFactory(ContentFactory[Dict[str, Any], List[IconRule]]):

    def __init__(self, rule_mapping: Dict[str, Type[IconRule]]) -> None:
        super().__init__()
        self.folder_builders = folder_builders(rule_mapping)
        self.chained_builder = ChainedRuleBuilder(rule_mapping=rule_mapping,
                                                  create_rule_func=self.create_folder_rule)

    def create_folder_rule(self, rule_config: Dict[str, Any], **kwargs) -> IconRule:
        for builder in self.folder_builders:
            if not builder.can_build(rule_config):
                continue
            return builder.create(rule_config, **kwargs)
        raise RuntimeError(f'No Folder builder could be created')

    def get_rule(self, rule_config: Dict[str, Any], **kwargs) -> IconRule:
        if self.chained_builder.can_build(rule_config):
            return self.chained_builder.create(rule_config, **kwargs)
        return self.create_folder_rule(rule_config, **kwargs)

    def create(self, rule_config: Dict[str, Any], **kwargs) -> List[IconRule]:
        filter_rules = []
        for rule_config in rule_config.get(ConfigKeys.RULES, []):
            filter_rule = self.get_rule(rule_config, **kwargs)
            filter_rules.append(filter_rule)
        return filter_rules


class RulesManagerFactory(ContentFactory[Dict[str, Any], RulesManager]):

    def __init__(self, rule_mapping: Dict[str, Type[IconRule]]) -> None:
        super().__init__()
        self.rule_factory = IconRuleFactory(rule_mapping)

    def create(self, rule_config: Dict[str, Any], **kwargs) -> RulesManager:
        attribute: str = kwargs.get(ConfigKeys.ATTRIBUTE, 'None')
        operator = get_operator(rule_config)
        rules = self.rule_factory.create(rule_config, **kwargs)
        return RulesManager(attribute, operator, rules)


class RuleConfigFactory(FileFactory[JsonFile, RuleConfig]):

    def __init__(self, rule_mapping: Dict[str, Type[IconRule]],
                 source: JsonSource = JsonSource()) -> None:
        self.manager_factory = RulesManagerFactory(rule_mapping)
        self.source = source
        self.__template: Dict[str, Any] = {}

    def is_config_file(self, entry: PathModel) -> bool:
        return JsonFile.is_model(entry.path)

    def get_config_section(self, icon_config: Dict[str, Any]) -> Dict[str, Any]:
        section = icon_config.get(ConfigKeys.CONFIG, None)
        if section is None:
            message = f'Key "{ConfigKeys.CONFIG}" does NOT exist in Setting'
            raise ValueError(message)
        if not isinstance(section, Dict):
            message = f'Expected Dict but got "{type(section)}"'
            raise ValueError(message)
        return section

    def get_rule_managers(self, icon_config: Dict[str, Any]) -> List[RulesManager]:
        managers = []
        for attribute, rules_dict in icon_config.items():
            manager = self.manager_factory.create(rule_config=rules_dict,
                                                  attribute=attribute)
            if manager.is_empty():
                continue
            managers.append(manager)
        return managers

    def create(self, config: JsonFile, **kwargs) -> RuleConfig:
        icon_config = self.source.read(config)
        config_section = self.get_config_section(icon_config)
        order = config_section.pop(ConfigKeys.ORDER, 5)
        operator = pop_operator(config_section, Operator.ALL)
        managers = self.get_rule_managers(config_section)
        return RuleConfig(config, managers, operator, order)

    def update(self, config: JsonFile, template_file: JsonFile) -> None:
        content = self.source.read(config)
        if len(self.__template) == 0:
            self.__template = self.source.read(template_file)
        for section, values in self.__template.items():
            if section == ConfigKeys.CONFIG:
                continue
            if content[section] == values:
                continue
            content[section] = values
        self.source.write(config, content)
        log.info(f'Updated config {config.name_wo_extension}')
