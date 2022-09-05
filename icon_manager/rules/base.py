from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, Iterable, TypeVar
from icon_manager.helpers.path import Folder

from icon_manager.interfaces.path import FolderModel


class Operator(str, Enum):
    UNKNOWN = 'unknown',
    ANY = 'any',
    ALL = 'all'


TValue = TypeVar('TValue', bound=object)
TEntry = TypeVar('TEntry', bound=object)


class FilterRule(ABC, Generic[TEntry, TValue]):

    def __init__(self, operator: Operator) -> None:
        super().__init__()
        self.operator = operator

    @abstractmethod
    def is_allowed(self, entry: TEntry) -> bool:
        pass

    def is_allowed_with_operator(self, entry: TEntry, value: TValue) -> bool:
        if self.operator == Operator.ALL:
            return self.are_all_allowed(entry, value)
        return self.are_any_allowed(entry, value)

    @ abstractmethod
    def are_any_allowed(self, entry: TEntry, value: TValue) -> bool:
        pass

    @ abstractmethod
    def are_all_allowed(self, entry: TEntry, value: TValue) -> bool:
        pass


class IconRule(FilterRule[Folder, str]):

    def __init__(self, attribute: str, operator: Operator) -> None:
        super().__init__(operator)
        self.attribute = attribute

    @abstractmethod
    def is_allowed(self, entry: Folder) -> bool:
        pass

    @ abstractmethod
    def are_any_allowed(self, entry: Folder, value: str) -> bool:
        pass

    @ abstractmethod
    def are_all_allowed(self, entry: Folder, value: str) -> bool:
        pass

    @ abstractmethod
    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        pass

    @ abstractmethod
    def generate_rule_values(self) -> None:
        pass
