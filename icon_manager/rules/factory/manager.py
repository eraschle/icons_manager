import logging
from abc import abstractmethod
from turtle import update
from typing import Any, Dict, Generic, Iterable, Optional, Sequence, TypeVar

from icon_manager.data.base import Source
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.resource import excluded_rules_template_file
from icon_manager.interfaces.factory import ContentFactory, FileFactory
from icon_manager.interfaces.path import ConfigFile, JsonFile
from icon_manager.rules.base import (IFilterRule, ISingleRule, Operator,
                                     RuleAttribute, get_rule_attribute)
from icon_manager.rules.factory.rules import (ConfigKeys, get_builders,
                                              get_operator, pop_operator)
from icon_manager.rules.manager import (AttributeChecker, ExcludeManager,
                                        RuleChecker, RuleManager)

log = logging.getLogger(__name__)


class AttributeCheckerFactory(ContentFactory[Dict[str, Any], AttributeChecker]):

    def __init__(self) -> None:
        super().__init__()
        self.builders = get_builders()

    def create_rule(self, rule_config: Dict[str, Any], **kwargs) -> IFilterRule:
        for builder in self.builders:
            if not builder.can_build(rule_config):
                continue
            return builder.create(rule_config, **kwargs)
        raise RuntimeError(f'No Folder builder could be created')

    def create_rules(self, config: Dict[str, Any], **kwargs) -> Sequence[ISingleRule]:
        rules = []
        for config in config.get(ConfigKeys.RULES, []):
            rule = self.create_rule(config, **kwargs)
            rules.append(rule)
        return rules

    def create(self, config: Dict[str, Any], **kwargs) -> AttributeChecker:
        attribute = kwargs.get(ConfigKeys.ATTRIBUTE, RuleAttribute.UNKNOWN)
        operator = pop_operator(config, Operator.ANY)
        rules = self.create_rules(config, **kwargs)
        return AttributeChecker(attribute, operator, rules)


class SourceCheckerBuilder(ContentFactory[Dict[str, Any], RuleChecker]):

    def __init__(self, source: Source = JsonSource()) -> None:
        self.source = source
        self.factory = AttributeCheckerFactory()

    def get_attribute_checkers(self, config: Dict[str, Any]) -> Sequence[AttributeChecker]:
        managers = []
        for attribute, rules_configs in config.items():
            rule_attr = get_rule_attribute(attribute)
            manager = self.factory.create(rules_configs, attribute=rule_attr)
            managers.append(manager)
        return managers

    def create(self, config: Dict[str, Any], **kwargs) -> RuleChecker:
        operator = pop_operator(config, Operator.ALL)
        managers = self.get_attribute_checkers(config)
        return RuleChecker(managers, operator)


TModel = TypeVar('TModel', bound=object, covariant=True)
TContent = TypeVar('TContent', bound=Iterable)


class AManagerFactory(FileFactory[JsonFile, TModel], Generic[TModel, TContent]):

    def __init__(self, source: Source = JsonSource()) -> None:
        self.source = source
        self.builder = SourceCheckerBuilder()
        self._template: Dict[str, Any] = {}

    def get_config_section(self, config: Dict[str, Any]) -> TContent:
        section: Optional[TContent] = config.get(ConfigKeys.CONFIG, None)
        if section is None:
            message = f'Key "{ConfigKeys.CONFIG}" does NOT'
            raise ValueError(message)
        return section

    def create(self, file: JsonFile, **kwargs) -> TModel:
        content = self.source.read(file)
        config = self.get_config_section(content)
        return self.create_with_content(config, file=file, ** kwargs)

    @abstractmethod
    def create_with_content(self, config: TContent, **kwargs) -> TModel:
        pass


class RuleManagerFactory(AManagerFactory[RuleManager, Dict[str, Any]]):

    def create_with_content(self, config: Dict[str, Any], **kwargs) -> RuleManager:
        file: Optional[JsonFile] = kwargs.get('file', None)
        if file is None:
            raise ValueError('"file" is not in kwargs or None')
        order = config.pop(ConfigKeys.ORDER, 5)
        manager = self.builder.create(config, **kwargs)
        return RuleManager(file, manager, order)

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
        log.info(f'Updated config {config.name_wo_extension}')


class ExcludeManagerFactory(AManagerFactory[ExcludeManager, Iterable[Dict[str, Any]]]):

    def create_with_content(self, config: Iterable[Dict[str, Any]], **kwargs) -> ExcludeManager:
        checkers = []
        for checker_config in config:
            checker = self.builder.create(checker_config, **kwargs)
            checkers.append(checker)
        return ExcludeManager(checkers)

    def copy_template(self, config: ConfigFile) -> None:
        template = excluded_rules_template_file()
        template.copy_to(config)

    def prepare_template(self, config: ConfigFile) -> None:
        content = self.source.read(config)
        self.source.write(config, content)

    def create_template(self, config: ConfigFile) -> ConfigFile:
        self.copy_template(config)
        self.prepare_template(config)
        return config
