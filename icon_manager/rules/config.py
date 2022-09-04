import logging
from abc import ABC, abstractmethod
from typing import Collection, Iterable, Protocol

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


class IRuleConfig(Protocol):

    def is_empty(self) -> bool:
        ...

    def rule_count(self) -> int:
        ...

    def has_rule_for(self, entry: Folder) -> bool:
        ...

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        ...


class ARuleConfig(ABC, IRuleConfig):

    def __init__(self, rule_managers: Collection[RulesManager]) -> None:
        self.rule_managers = rule_managers

    def is_empty(self) -> bool:
        if len(self.rule_managers) == 0:
            return True
        return False

    def rule_count(self) -> int:
        return sum([man.rule_count() for man in self.rule_managers])

    @abstractmethod
    def has_rule_for(self, entry: Folder) -> bool:
        pass

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        for rule_manager in self.rule_managers:
            rule_manager.set_before_or_after(before_or_after)


class RuleConfig(ARuleConfig):

    def __init__(self, config: JsonFile,
                 rule_managers: Collection[RulesManager],
                 operator: Operator, weight: int) -> None:
        super().__init__(rule_managers)
        self.config = config
        self.operator = operator
        self.order_weight = weight

    @ property
    def name(self) -> str:
        return self.config.name_wo_extension

    def has_rule_for(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            has_rule = all(man.is_allowed(entry) for man in self.rule_managers)
        else:
            has_rule = any(man.is_allowed(entry) for man in self.rule_managers)
        if has_rule:
            log.debug(f'Icon rule matches {entry.name}')
        return has_rule

    def __str__(self) -> str:
        return f'Icon Rule Config [{self.rule_count()} Rules]'


class ExcludeRuleConfig(ARuleConfig):

    def __str__(self) -> str:
        return f'Exclude Rule Config [{self.rule_count()} Rules]'

    def has_rule_for(self, entry: Folder) -> bool:
        has_rule = any(man.is_allowed(entry) for man in self.rule_managers)
        if has_rule:
            log.debug(f'Exclude Rule matches  {entry.name}')
        return has_rule
