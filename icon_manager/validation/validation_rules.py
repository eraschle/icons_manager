from typing import Sequence

from icon_manager.rules.base import Operator, RuleAttribute
from icon_manager.validation.base.validator import ValidationRule


class KnownRuleAttributeRule(ValidationRule[RuleAttribute]):

    def apply(self) -> bool:
        """
        Return True if the rule attribute is known (not UNKNOWN); otherwise, return False.
        """
        return self.apply_to != RuleAttribute.UNKNOWN


class KnownOperatorRule(ValidationRule[Operator]):

    def apply(self) -> bool:
        """
        Return True if the operator is not UNKNOWN.
        
        Returns:
            bool: True if the operator is known; False otherwise.
        """
        return self.apply_to != Operator.UNKNOWN


class RuleValuesRule(ValidationRule[Sequence[str]]):

    def apply(self) -> bool:
        """
        Return True if the sequence of values is non-empty; otherwise, return False.
        """
        return len(self.apply_to) > 0


class PathOperationAttributeRule(ValidationRule[RuleAttribute]):

    def apply(self) -> bool:
        """
        Return True if the rule attribute is either PATH or PARENT_PATH.
        
        Returns:
            bool: True if the attribute is PATH or PARENT_PATH; otherwise, False.
        """
        return self.apply_to in (RuleAttribute.PATH, RuleAttribute.PARENT_PATH)
