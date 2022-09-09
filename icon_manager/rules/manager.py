import logging
from typing import Iterable, Optional, Sequence

from icon_manager.interfaces.path import Folder
from icon_manager.interfaces.managers import (IAttributeChecker, IChecker,
                                              IRuleChecker)
from icon_manager.interfaces.path import JsonFile
from icon_manager.rules.base import ISingleRule, Operator, RuleAttribute

log = logging.getLogger(__name__)


class AttributeChecker(IAttributeChecker[Folder]):

    def __init__(self, attribute: RuleAttribute, operator: Operator,
                 rules: Sequence[ISingleRule]) -> None:
        self.attribute = attribute
        self.operator = operator
        self.rules = rules

    @property
    def name(self) -> str:
        return f'"{self.attribute.upper()}" Checker'

    def is_empty(self) -> bool:
        return all(rule.is_empty() for rule in self.rules)

    def clean_empty(self) -> None:
        rules = []
        for rule in self.rules:
            if rule.is_empty():
                continue
            rules.append(rule)
        self.rules = rules

    def is_allowed(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(rule.is_allowed(entry) for rule in self.rules)
        return any(rule.is_allowed(entry) for rule in self.rules)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for rule in self.rules:
            rule.set_before_or_after(before_or_after)
            rule.setup_filter_rule()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class RuleChecker(IRuleChecker[Folder]):

    def __init__(self, checkers: Sequence[AttributeChecker],
                 operator: Operator) -> None:
        self.checkers = checkers
        self.operator = operator

    @property
    def name(self) -> str:
        attributes = ', '.join([checker.attribute.name
                               for checker in self.checkers])
        return f'Rule Checker [{attributes}]'

    def is_empty(self) -> bool:
        return all(checker.is_empty() for checker in self.checkers)

    def clean_empty(self) -> None:
        checkers = []
        for checker in self.checkers:
            checker.clean_empty()
            if checker.is_empty():
                continue
            checkers.append(checker)
        self.checkers = checkers

    def is_allowed(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(checker.is_allowed(entry) for checker in self.checkers)
        return any(rule.is_allowed(entry) for rule in self.checkers)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for checker in self.checkers:
            checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class RuleManager(IChecker[Folder]):

    def __init__(self, config: JsonFile, checker: RuleChecker, weight: int, copy_icon: Optional[bool]) -> None:
        self.config = config
        self.checker = checker
        self.weight = weight
        self.copy_icon = copy_icon

    @property
    def name(self) -> str:
        return self.config.name_wo_extension

    def is_empty(self) -> bool:
        return self.checker.is_empty()

    def clean_empty(self) -> None:
        self.checker.clean_empty()

    def is_allowed(self, entry: Folder) -> bool:
        return self.checker.is_allowed(entry)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        self.checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        name = self.config.name_wo_extension.upper()
        return f'"{name}" Manager'

    def __repr__(self) -> str:
        return self.__str__()


class ExcludeManager(IChecker[Folder]):

    def __init__(self, checkers: Sequence[IRuleChecker[Folder]]) -> None:
        self.checkers = checkers

    def is_empty(self) -> bool:
        return all(checker.is_empty() for checker in self.checkers)

    def is_valid(self) -> bool:
        return all(checker.is_valid() for checker in self.checkers)

    def clean_empty(self) -> None:
        checkers = []
        for checker in self.checkers:
            checker.clean_empty()
            if checker.is_empty():
                continue
            checkers.append(checker)
        self.checkers = checkers

    def is_allowed(self, entry: Folder) -> bool:
        if self.is_empty():
            return True
        return any(manager.is_allowed(entry) for manager in self.checkers)

    def is_excluded(self, entry: Folder) -> bool:
        if self.is_empty():
            return False
        return self.is_allowed(entry)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for checker in self.checkers:
            checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        return f'Exclude Manager [{len(self.checkers)}]'

    def __repr__(self) -> str:
        return self.__str__()
