import logging
from typing import Collection, Iterable

from icon_manager.helpers.path import Folder
from icon_manager.interfaces.path import JsonFile
from icon_manager.rules.base import IconRule, Operator
from icon_manager.rules.rules import ChainedRule

log = logging.getLogger(__name__)


class RulesManager(ChainedRule):

    def __init__(self, attribute: str, operator: Operator,
                 rules: Collection[IconRule]) -> None:
        super().__init__(attribute, operator, rules)

    def is_allowed(self, folder: Folder) -> bool:
        if self.rule_count() == 0:
            return True
        return super().is_allowed(folder)


class RuleConfig:
    def __init__(self, config: JsonFile,
                 rule_managers: Collection[RulesManager],
                 operator: Operator, weight: int) -> None:
        self.config = config
        self.rule_managers = rule_managers
        self.operator = operator
        self.order_weight = weight

    @ property
    def path(self) -> str:
        return self.config.path

    @ property
    def name(self) -> str:
        return self.config.name_wo_extension

    def is_empty(self) -> bool:
        if len(self.rule_managers) == 0:
            return True
        return all(manager.is_empty() for manager in self.rule_managers)

    def is_config_for(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(manager.is_allowed(entry) for manager in self.rule_managers)
        return any(manager.is_allowed(entry) for manager in self.rule_managers)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        for rule_manager in self.rule_managers:
            rule_manager.set_before_or_after(before_or_after)

    def __str__(self) -> str:
        return f'Icon Rule Config: {self.config.name_wo_extension}'

    def __repr__(self) -> str:
        output = self.__str__()
        for manager in self.rule_managers:
            output = f'{output} {manager.attribute} [{manager.rule_count()}]'
        return output
