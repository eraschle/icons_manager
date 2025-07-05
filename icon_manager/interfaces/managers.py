import logging
from typing import Generic, Iterable, Sequence, TypeVar

from icon_manager.rules.base import (ISingleRule, Operator, RuleAttribute,
                                     RuleProtocol)

log = logging.getLogger(__name__)

TModel = TypeVar('TModel', bound=object, contravariant=True)


class IRuleController(Generic[TModel], RuleProtocol[TModel]):
    operator: Operator

    @property
    def name(self) -> str:
        """
        Returns the name of the rule controller.
        """
        ...

    def is_empty(self) -> bool:
        """
        Return True if the rule controller contains no rules or conditions; otherwise, return False.
        """
        ...

    def clean_empty(self) -> None:
        """
        Remove or clean up any empty or invalid rules from the controller.
        """
        ...

    def is_allowed(self, entry: TModel) -> bool:
        ...

    def setup_rules(self, values: Iterable[str]) -> None:
        """
        Initialize or configure rules based on the provided iterable of string values.
        
        Parameters:
            values (Iterable[str]): An iterable of string representations used to set up rules.
        """
        ...


class IAttributeRuleController(IRuleController[TModel]):
    attribute: RuleAttribute
    operator: Operator
    rules: Sequence[ISingleRule]

    @property
    def name(self) -> str:
        """
        Returns the name of the rule controller.
        """
        ...

    def is_empty(self) -> bool:
        ...

    def clean_empty(self) -> None:
        ...

    def is_allowed(self, entry: TModel) -> bool:
        ...

    def setup_rules(self, values: Iterable[str]) -> None:
        """
        Initialize or configure rules based on the provided iterable of string values.
        
        Parameters:
            values (Iterable[str]): An iterable of string representations used to set up rules.
        """
        ...


class IConfigRuleController(IRuleController[TModel]):
    operator: Operator
    controllers: Sequence[IAttributeRuleController]

    @property
    def name(self) -> str:
        """
        Returns the name of the rule controller.
        """
        ...

    def is_empty(self) -> bool:
        """
        Return True if the rule controller contains no rules or conditions; otherwise, return False.
        """
        ...

    def clean_empty(self) -> None:
        """
        Remove or clean up any empty or invalid rules from the controller.
        """
        ...

    def is_allowed(self, entry: TModel) -> bool:
        """
        Determines whether the given entry satisfies all configured rules.
        
        Parameters:
            entry (TModel): The model instance to evaluate against the rules.
        
        Returns:
            bool: True if the entry is allowed according to the rules, False otherwise.
        """
        ...

    def setup_rules(self, values: Iterable[str]) -> None:
        """
        Initialize or configure rules based on the provided iterable of string values.
        
        Parameters:
            values (Iterable[str]): An iterable of string representations used to set up rules.
        """
        ...


class IConfigManager(IRuleController[TModel]):
    controller: IConfigRuleController

    @property
    def name(self) -> str:
        """
        Returns the name of the rule controller.
        """
        ...

    def is_empty(self) -> bool:
        """
        Return True if the rule controller contains no rules or conditions; otherwise, return False.
        """
        ...

    def clean_empty(self) -> None:
        """
        Remove or clean up any empty or invalid rules from the controller.
        """
        ...

    def is_allowed(self, entry: TModel) -> bool:
        ...

    def setup_rules(self, values: Iterable[str]) -> None:
        """
        Initialize or configure rules based on the provided iterable of string values.
        
        Parameters:
            values (Iterable[str]): An iterable of string representations used to set up rules.
        """
        ...

    def validate(self) -> str:
        """
        Validate the current configuration and return the validation result as a string.
        
        Returns:
            str: A message indicating the outcome of the validation, such as an error description or success status.
        """
        ...
