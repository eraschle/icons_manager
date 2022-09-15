from typing import List, Type

from icon_manager.rules.base import IFilterRule, Operator
from icon_manager.rules.rules import (ContainsRule, EqualsRule,
                                      IPathOperationRule, IRuleValuesFilter,
                                      NotContainsRule, NotEqualsRule)
from icon_manager.validation.base.validator import ConsiderRule

# region GENERAL CONSIDERATIONS


class ShortRuleValueConsideration(ConsiderRule[IFilterRule]):
    length_short = 2

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return (isinstance(rule, IRuleValuesFilter)
                and not isinstance(rule, (EqualsRule, NotEqualsRule)))

    def __init__(self, apply_to: IFilterRule):
        super().__init__(apply_to, label='rule value length',
                         consideration=f'Short rule values [less then {self.__class__.length_short}] can have many hits')

    def apply(self):
        if not isinstance(self.apply_to, IRuleValuesFilter):
            return False
        if isinstance(self.apply_to, (EqualsRule, NotEqualsRule)):
            return False
        length_short = self.__class__.length_short
        return (any(len(value) < length_short for value in self.apply_to.rule_values)
                and (len(self.apply_to.rule_values) == 1
                     or
                     len(self.apply_to.rule_values) > 1 and self.apply_to.operator == Operator.ANY))


class EqualsRuleAndAllConsideration(ConsiderRule[EqualsRule]):

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return isinstance(rule, (EqualsRule, NotEqualsRule))

    def __init__(self, apply_to: EqualsRule):
        super().__init__(apply_to, label='(Not) equals with ALL',
                         consideration='Equals rule with more then one rule value and ALL is always FALSE')

    def apply(self) -> bool:
        return len(self.apply_to.rule_values) > 1 and self.apply_to.operator == Operator.ALL


class ContainsRuleAndAnyConsideration(ConsiderRule[ContainsRule]):

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        super().__init__(apply_to, label='(Not) contains with ANY',
                         consideration='contains rule with more then one rule value and ANY is always TRUE')

    def apply(self) -> bool:
        return len(self.apply_to.rule_values) > 1 and self.apply_to.operator == Operator.ANY


class ContainsShortRuleValueConsideration(ConsiderRule[ContainsRule]):
    length_short = 4

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        super().__init__(apply_to, label='contains rule length and operator',
                         consideration=f'Contains rule with short rule values [{self.__class__.length_short}] '
                         f'and ANY can have many hits')

    def apply(self):
        length_short = self.__class__.length_short
        if not any(len(value) < length_short for value in self.apply_to.rule_values):
            return False
        return self.apply_to.operator == Operator.ANY


class ContainsWithBeforeAndAfterConsideration(ConsiderRule[ContainsRule]):

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        super().__init__(apply_to, label='contains with before and after',
                         consideration=f'Contains Rule return also TRUE without generating before and after values')

    def apply(self):
        return self.apply_to.add_before_or_after_values == True


# endregion


# region PATH OPERATIONS CONSIDERATIONS


class PathAndGreatLevelConsideration(ConsiderRule[IPathOperationRule]):
    max_levels = 4

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        return isinstance(rule, IPathOperationRule)

    def __init__(self, apply_to: IPathOperationRule):
        super().__init__(apply_to, label='path rules and max_level',
                         consideration=f'Many levels are slow  [greater then {self.__class__.max_levels}].'
                         f'Does it REALLY need a dependency on files or folders deep in the file system')

    def apply(self):
        return self.apply_to.max_level > self.__class__.max_levels


# endregion


def _considerations() -> List[Type[ConsiderRule]]:
    rules: List[Type[ConsiderRule]] = []
    for name, value in globals().items():
        if not name.endswith('Consideration'):
            continue
        if not issubclass(value, ConsiderRule):
            continue
        rules.append(value)
    return rules


def get_considerations(filter_rule: IFilterRule) -> List[ConsiderRule[IFilterRule]]:
    return [rule(filter_rule) for rule in _considerations()
            if rule.is_consideration(filter_rule)]
