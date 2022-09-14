from typing import Optional, TypeVar

from icon_manager.rules.base import IFilterRule
from icon_manager.validation.base.validator import ConsiderationRule

DATA_ERRORS = (TypeError, IndexError, KeyError,
               NameError, ValueError, AttributeError)

TFilterRule = TypeVar('TFilterRule', bound=IFilterRule)


class TypeRule(ConsiderationRule[TFilterRule]):
    #: Default error message for the rule.
    default_consideration_message = 'Object is not an instance of the expected type.'

    def __init__(self, apply_to: TFilterRule, label: str, valid_type: type,
                 error_message: Optional[str] = None):
        super().__init__(apply_to, label, error_message)
        self.valid_type = valid_type

    def apply(self) -> bool:
        return isinstance(self.apply_to, self.valid_type)


class FullStringRule(ConsiderationRule[TFilterRule]):
    #: Default error message for the rule.
    default_consideration_message = 'String is empty.'

    def __init__(self, apply_to: TFilterRule, label: str,
                 error_message: Optional[str] = None):
        super().__init__(apply_to, label, error_message)

    def apply(self):
        value = self.apply_to
        return isinstance(value, str) and len(value.strip()) > 0
