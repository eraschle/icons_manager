import logging
from typing import Generic, TypeVar

from icon_manager.rules.base import (
    IFilterRule,
    IRuleValidator,
    Operator,
    Rule,
    RuleAttribute,
)
from icon_manager.rules.rules import ChainedRule, ContainsFileRule

log = logging.getLogger(__name__)


TRule = TypeVar("TRule", bound=IFilterRule, contravariant=True)


class FilterRuleValidator(IRuleValidator, Generic[TRule]):
    @classmethod
    def rule(cls) -> Rule:
        return Rule.UNKNOWN

    def __init__(self, filter_rule: TRule) -> None:
        self.filter_rule = filter_rule

    def is_valid(self) -> bool:
        return self.filter_rule.attribute != RuleAttribute.UNKNOWN and self.filter_rule.operator != Operator.UNKNOWN


class ContainsFileRuleValidator(FilterRuleValidator[ContainsFileRule]):
    @classmethod
    def rule(cls) -> Rule:
        return Rule.CONTAINS_FILE

    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        return self.filter_rule.attribute == RuleAttribute.PATH


class ChainedRuleValidator(FilterRuleValidator[ChainedRule]):
    @classmethod
    def rule(cls) -> Rule:
        return Rule.CHAINED

    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        return all(rule.is_valid() for rule in self.rule.rules)
