import logging
from typing import Generic, Iterable, Sequence, TypeVar
from collections.abc import Iterable
from typing import Generic, TypeVar

from icon_manager.rules.base import (ISingleRule, Operator, RuleAttribute,
                                     RuleProtocol)

log = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=object, contravariant=True)


class IRuleController(Generic[TModel], RuleProtocol[TModel]):
    operator: Operator

    @property
    def name(self) -> str:
        ...

    def is_empty(self) -> bool:
        ...

    def clean_empty(self) -> None: ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None: ...


class IAttributeRuleController(IRuleController[TModel]):
    attribute: RuleAttribute
    operator: Operator
    rules: Sequence[ISingleRule]

    @property
    def name(self) -> str: ...

    def is_empty(self) -> bool: ...

    def clean_empty(self) -> None: ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None: ...


class IConfigRuleController(IRuleController[TModel]):
    operator: Operator
    controllers: Sequence[IAttributeRuleController]

    @property
    def name(self) -> str: ...

    def is_empty(self) -> bool: ...

    def clean_empty(self) -> None:
        ...

    def is_allowed(self, entry: TModel) -> bool: ...

    def setup_rules(self, values: Iterable[str]) -> None:
        ...


class IConfigManager(IRuleController[TModel]):
    controller: IConfigRuleController

    @property
    def name(self) -> str:
        ...

    def is_empty(self) -> bool:
        ...

    def clean_empty(self) -> None:
        ...

    def is_allowed(self, entry: TModel) -> bool:
        ...

    def setup_rules(self, values: Iterable[str]) -> None:
        ...

    def validate(self) -> str:
        ...
