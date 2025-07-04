import logging
from collections.abc import Iterable
from typing import Generic, TypeVar

from icon_manager.rules.base import Operator, RuleAttribute, RuleProtocol

log = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=object, contravariant=True)


class IChecker(Generic[TModel], RuleProtocol[TModel]):
    operator: Operator

    def is_empty(self) -> bool: ...

    def is_valid(self) -> bool: ...

    def clean_empty(self) -> None: ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None: ...


class IAttributeChecker(IChecker[TModel]):
    attribute: RuleAttribute
    operator: Operator

    @property
    def name(self) -> str: ...

    def is_empty(self) -> bool: ...

    def clean_empty(self) -> None: ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None: ...


class IRuleChecker(IChecker[TModel]):
    operator: Operator

    @property
    def name(self) -> str: ...

    def is_empty(self) -> bool: ...

    def is_valid(self) -> bool: ...

    def clean_empty(self) -> None: ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None: ...
