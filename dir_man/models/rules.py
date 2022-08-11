from abc import ABC, abstractmethod
from enum import Enum
from typing import Iterable

# region RULES INTERFACE


class Operator(str, Enum):
    UNKNOWN = 'unknown',
    ANY = 'any',
    ALL = 'all'


def get_operator(operator_value: str) -> Operator:
    operator_value = operator_value.lower()
    for operator in Operator:
        if operator != operator_value:
            continue
        return operator
    return Operator.UNKNOWN


class FolderRule(ABC):
    def __init__(self, attribute: str, values: Iterable[str], operator: str,
                 case_sensitive: bool) -> None:
        self.attribute = attribute
        self.__values = values
        self.operator = get_operator(operator)
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
    def values(self) -> Iterable[str]:
        return self.get_case_sensitive_values(self.__values)

    def is_allowed(self, folder: object) -> bool:
        attribute_value = getattr(folder, self.attribute, None)
        if attribute_value is None or self.operator == Operator.UNKNOWN:
            return False
        attribute_value = self.get_case_sensitive_value(attribute_value)
        bool_mask = self.is_value_allowed(attribute_value)
        return all(bool_mask) if self.operator == Operator.ALL else any(bool_mask)

    @abstractmethod
    def is_value_allowed(self, attribute_value: str) -> Iterable[bool]:
        pass

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute} {self.values}'

    def __repr__(self) -> str:
        return self.__str__()


# endregion


# region CONCRETE RULES


class EqualsRule(FolderRule):
    def is_value_allowed(self, attribute_value: str) -> Iterable[bool]:
        return [value == attribute_value for value in self.values]


class ContainsRule(FolderRule):
    def is_value_allowed(self, attribute_value: str) -> Iterable[bool]:
        return [value in attribute_value for value in self.values]


class NotContainsRule(ContainsRule):
    def is_value_allowed(self, attribute_value: str) -> Iterable[bool]:
        bool_mask = super().is_value_allowed(attribute_value)
        return [value is False for value in bool_mask]


# endregion
