import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Collection, Iterable, List, Protocol

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
                 operator: Operator, case_sensitive: bool, before_or_after: Collection[str]) -> None:
        self.attribute = attribute
        self.__values = values
        self.operator = operator
        self.case_sensitive = case_sensitive
        self.before_or_after = before_or_after

    def get_case_sensitive_value(self, value: str) -> str:
        if self.case_sensitive:
            return value
        return value.lower()

    def get_case_sensitive_values(self, values: Iterable[str]) -> Iterable[str]:
        if self.case_sensitive:
            return values
        return [self.get_case_sensitive_value(value) for value in values]

    def get_before_value(self, value: str) -> Iterable[str]:
        return [f'{before}{value}' for before in self.before_or_after]

    def get_after_value(self, value: str) -> Iterable[str]:
        return [f'{after}{value}' for after in self.before_or_after]

    def get_before_and_after_value(self, value: str) -> Iterable[str]:
        return [f'{extra}{value}{extra}' for extra in self.before_or_after]

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return [self.get_before_value, self.get_after_value, self.get_before_and_after_value]

    def get_before_or_after_value(self, value: str) -> Iterable[str]:
        before_or_after: List[str] = []
        for create_values in self.get_before_or_after_callables():
            before_or_after.extend(create_values(value))
        return before_or_after

    def get_before_or_after_values(self, values: Iterable[str]) -> Iterable[str]:
        if len(self.before_or_after) == 0:
            return values
        before_or_after: List[str] = []
        for value in values:
            before_or_after.append(value)
            before_or_after.extend(self.get_before_or_after_value(value))
        return before_or_after

    @ property
    def rule_values(self) -> Iterable[str]:
        values = self.get_case_sensitive_values(self.__values)
        return self.get_before_or_after_values(values)

    def is_allowed(self, folder: object) -> bool:
        attribute_value = getattr(folder, self.attribute, None)
        if attribute_value is None or self.operator == Operator.UNKNOWN:
            return False
        attribute_value = self.get_case_sensitive_value(attribute_value)
        if self.operator == Operator.ALL:
            return self.are_all_values_allowed(attribute_value)
        return self.are_any_values_allowed(attribute_value)

    def are_any_values_allowed(self, attribute_value: str) -> bool:
        return any(self.is_values_allowed(attribute_value, value) for value in self.rule_values)

    def are_all_values_allowed(self, attribute_value: str) -> bool:
        return all(self.is_values_allowed(attribute_value, value) for value in self.rule_values)

    @abstractmethod
    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        pass

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute} {self.rule_values}'

    def __repr__(self) -> str:
        return self.__str__()


# endregion


# region CONCRETE RULES


class EqualsRule(FolderRule):

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return rule_value == attribute_value


class NotEqualsRule(EqualsRule):

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return not super().is_values_allowed(attribute_value, rule_value)


class ContainsRule(FolderRule):

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return [self.get_before_value, self.get_after_value]

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return rule_value in attribute_value


class NotContainsRule(ContainsRule):

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return not super().is_values_allowed(attribute_value, rule_value)


class StartswithRule(FolderRule):

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return [self.get_before_value, self.get_after_value]

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return attribute_value.startswith(rule_value)


class EndswithRule(FolderRule):

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return [self.get_before_value, self.get_after_value]

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return attribute_value.endswith(rule_value)


class StartsOrEndswithRule(FolderRule):

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return [self.get_before_value, self.get_after_value]

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        return attribute_value.startswith(rule_value) or attribute_value.endswith(rule_value)


class ContainsExtensionRule(FolderRule):

    def __init__(self, attribute: str, values: Iterable[str],
                 operator: Operator, case_sensitive: bool,
                 before_or_after: Collection[str], level: int) -> None:
        super().__init__(attribute, values, operator, case_sensitive, before_or_after)
        self.max_level = level

    def get_before_or_after_callables(self) -> Iterable[Callable[[str], Iterable[str]]]:
        return []

    def get_files(self, full_path: str, level: int) -> List[str]:
        files: List[str] = []
        if level > self.max_level:
            return files
        level += 1
        for name in os.listdir(full_path):
            path = os.path.join(full_path, name)
            if os.path.isdir(path):
                files.extend(self.get_files(path, level))
            elif any(name.endswith(value) for value in self.rule_values):
                files.append(name)
        return files

    def is_values_allowed(self, attribute_value: str, rule_value: str) -> bool:
        files = self.get_files(attribute_value, level=1)
        return any(file.endswith(rule_value) for file in files)


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
