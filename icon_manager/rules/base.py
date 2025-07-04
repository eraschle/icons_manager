from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Generic, Protocol, TypeVar

from icon_manager.interfaces.path import Folder


class Operator(str, Enum):
    UNKNOWN = ("unknown",)
    ANY = ("any",)
    ALL = "all"


class RuleAttribute(str, Enum):
    UNKNOWN = ("unknown",)
    NAME = "name"
    PATH = "path"
    PARENT_NAME = "parent_name"
    PARENT_PATH = "parent_path"


def get_rule_attribute(value) -> RuleAttribute:
    if not isinstance(value, str):
        return RuleAttribute.UNKNOWN
    for attr in RuleAttribute:
        if value.lower() != attr.value:
            continue
        return attr
    return RuleAttribute.UNKNOWN


TEntry = TypeVar("TEntry", bound=object, contravariant=True)


class IRuleValidator:
    def is_valid(self) -> bool: ...

    def message(self) -> bool: ...


class RuleProtocol(Protocol, Generic[TEntry]):
    operator: Operator

    def is_allowed(self, entry: TEntry) -> bool: ...


class IFilterRule(RuleProtocol[Folder]):
    operator: Operator
    attribute: RuleAttribute

    @property
    def name(self) -> str: ...

    def is_allowed(self, entry: Folder) -> bool: ...

    def is_empty(self) -> bool: ...


class Rule(str, Enum):
    UNKNOWN = ("unknown",)
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    STARTS_OR_ENDS_WITH = "start_or_ends_with"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    CHAINED = "chained"
    CONTAINS_FILE = "contains_file"
    NOT_CONTAINS_FILE = "not_contains_file"
    CONTAINS_FOLDER = "contains_folder"
    NOT_CONTAINS_FOLDER = "not_contains_folder"


def get_rule(value) -> Rule:
    if not isinstance(value, str):
        return Rule.UNKNOWN
    for rule in Rule:
        if value.lower() != rule.value:
            continue
        return rule
    return Rule.UNKNOWN


class AFilterRule(ABC, IFilterRule):
    def __init__(self, attribute: RuleAttribute, operator: Operator) -> None:
        super().__init__()
        self.attribute = attribute
        self.operator = operator

    @property
    def name(self) -> str:
        name = self.__class__.__name__.replace("Rule", "")
        return f"{name} Rule {self.attribute.name} [{self.operator.name}] "

    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_allowed(self, entry: Folder) -> bool:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name} {self.attribute} [{self.operator.name}]"


class ISingleRule(IFilterRule):
    operator: Operator
    attribute: RuleAttribute

    @property
    def name(self) -> str: ...

    @property
    def validator(self) -> IRuleValidator: ...

    def is_allowed(self, entry: Folder) -> bool: ...

    def is_empty(self) -> bool: ...

    def set_before_or_after(self, values: Iterable[str]) -> None: ...

    def setup_filter_rule(self) -> None: ...


class ASingleRule(AFilterRule, ISingleRule):
    @property
    def name(self) -> str:
        return f"Rule {self.attribute.name} [{self.operator.name}] "

    def is_allowed(self, entry: Folder) -> bool:
        value = getattr(entry, self.attribute.value, None)
        if value is None or self.operator == Operator.UNKNOWN:
            return False
        value = self.prepare_element_value(value)
        return self.is_allowed_with_operator(entry, value)

    def is_allowed_with_operator(self, entry: Folder, value: str) -> bool:
        if self.operator == Operator.ALL:
            return self.are_all_allowed(entry, value)
        return self.are_any_allowed(entry, value)

    @abstractmethod
    def prepare_element_value(self, value: str) -> str:
        pass

    @abstractmethod
    def are_any_allowed(self, entry: Folder, value: str) -> bool:
        pass

    @abstractmethod
    def are_all_allowed(self, entry: Folder, value: str) -> bool:
        pass
