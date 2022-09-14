
from typing import Sequence

from icon_manager.rules.base import Operator, RuleAttribute
from icon_manager.validation.base.validator import ValidationRule


class KnownRuleAttributeRule(ValidationRule[RuleAttribute]):

    def apply(self) -> bool:
        return self.apply_to != RuleAttribute.UNKNOWN


class KnownOperatorRule(ValidationRule[Operator]):

    def apply(self) -> bool:
        return self.apply_to != Operator.UNKNOWN


class RuleValuesRule(ValidationRule[Sequence[str]]):

    def apply(self) -> bool:
        return len(self.apply_to) > 0


class PathOperationAttributeRule(ValidationRule[RuleAttribute]):

    def apply(self) -> bool:
        return self.apply_to in (RuleAttribute.PATH, RuleAttribute.PARENT_PATH)
