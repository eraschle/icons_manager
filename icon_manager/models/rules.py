from abc import ABC, abstractmethod
from enum import Enum
from typing import Collection, Iterable, Protocol

# region RULES INTERFACE


class Operator(str, Enum):
    UNKNOWN = 'unknown',
    ANY = 'any',
    ALL = 'all'


class FilterRule(Protocol):

    def is_allowed(self, folder: object) -> bool:
        ...


class FolderRule(ABC, FilterRule):
    def __init__(self, attribute: str, values: Iterable[str],
                 operator: Operator, case_sensitive: bool) -> None:
        self.attribute = attribute
        self.__values = values
        self.operator = operator
        self.case_sensitive = case_sensitive

    def get_case_sensitive_value(self, value: str) -> str:
        if self.case_sensitive:
            return value
        return value.lower()

    def get_case_sensitive_values(self, values: Iterable[str]) -> Iterable[str]:
        if self.case_sensitive:
            return values
        return [self.get_case_sensitive_value(value) for value in values]

    @property
    def rule_values(self) -> Iterable[str]:
        return self.get_case_sensitive_values(self.__values)

    def is_allowed(self, folder: object) -> bool:
        attribute_value = getattr(folder, self.attribute, None)
        if attribute_value is None or self.operator == Operator.UNKNOWN:
            return False
        attribute_value = self.get_case_sensitive_value(attribute_value)
        if self.operator == Operator.ALL:
            return self.are_all_values_allowed(attribute_value)
        return self.are_any_values_allowed(attribute_value)

    @abstractmethod
    def are_any_values_allowed(self, attribute_value: str) -> bool:
        pass

    @abstractmethod
    def are_all_values_allowed(self, attribute_value: str) -> bool:
        pass

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute} {self.rule_values}'

    def __repr__(self) -> str:
        return self.__str__()


# endregion


# region CONCRETE RULES


class EqualsRule(FolderRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(value == attribute_value for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(value == attribute_value for value in self.rule_values)


class NotEqualsRule(FolderRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(value != attribute_value for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(value != attribute_value for value in self.rule_values)


class ContainsRule(FolderRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(value in attribute_value for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(value in attribute_value for value in self.rule_values)


class NotContainsRule(ContainsRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(value not in attribute_value for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(value not in attribute_value for value in self.rule_values)


class StartswithRule(FolderRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(attribute_value.startswith(value) for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(attribute_value.startswith(value) for value in self.rule_values)


class EndswithRule(FolderRule):

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(attribute_value.endswith(value) for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(attribute_value.endswith(value) for value in self.rule_values)


class StartsOrEndswithRule(FolderRule):

    def __is_allowed(self, attr_value: str, value: str) -> bool:
        return attr_value.startswith(value) or attr_value.endswith(value)

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(self.__is_allowed(attribute_value, value) for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(self.__is_allowed(attribute_value, value) for value in self.rule_values)


class ChainedRules(FilterRule):

    def __init__(self, rules: Iterable[FolderRule], operator: Operator) -> None:
        self.rules = rules
        self.operator = operator

    def is_allowed(self, folder: object) -> bool:
        if self.operator == Operator.ALL:
            return all(rule.is_allowed(folder) for rule in self.rules)
        return any(rule.is_allowed(folder) for rule in self.rules)


# endregion


class FilterRuleManager(FilterRule):
    def __init__(self, attribute: str, rules: Collection[FilterRule], operator: Operator) -> None:
        self.attribute = attribute
        self.rules = rules
        self.operator = operator

    def is_empty(self) -> bool:
        return self.rule_count() == 0

    def rule_count(self) -> int:
        return len(self.rules)

    def is_allowed(self, folder: object) -> bool:
        if self.rule_count() == 0:
            return True
        if self.operator == Operator.ALL:
            return all(rule.is_allowed(folder) for rule in self.rules)
        return any(rule.is_allowed(folder) for rule in self.rules)
