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
        """
        Determine if the rule is an instance of IRuleValuesFilter but not EqualsRule or NotEqualsRule.
        
        Returns:
            bool: True if the rule should be considered for short value analysis; otherwise, False.
        """
        return (isinstance(rule, IRuleValuesFilter)
                and not isinstance(rule, (EqualsRule, NotEqualsRule)))

    def __init__(self, apply_to: IFilterRule):
        """
        Initializes the consideration for short rule values that may produce many matches.
        
        Parameters:
            apply_to (IFilterRule): The filter rule instance to which this consideration applies.
        """
        super().__init__(apply_to, label='rule value length',
                         consideration=f'Short rule values [less then {self.__class__.length_short}] can have many hits')

    def apply(self):
        """
        Determine if a rule (excluding equals and not-equals rules) contains at least one value shorter than the defined threshold and is configured to match with either a single value or multiple values using the ANY operator.
        
        Returns:
            bool: True if the rule meets the criteria for short values that may cause excessive matches; otherwise, False.
        """
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
        """
        Determine if the given rule is an instance of EqualsRule or NotEqualsRule.
        
        Returns:
            bool: True if the rule is an EqualsRule or NotEqualsRule; otherwise, False.
        """
        return isinstance(rule, (EqualsRule, NotEqualsRule))

    def __init__(self, apply_to: EqualsRule):
        """
        Initialize the consideration for equals or not-equals rules with multiple values and the ALL operator.
        
        Parameters:
            apply_to (EqualsRule): The equals or not-equals rule instance to which this consideration applies.
        """
        super().__init__(apply_to, label='(Not) equals with ALL',
                         consideration='Equals rule with more then one rule value and ALL is always FALSE')

    def apply(self) -> bool:
        """
        Return True if the rule has multiple values and uses the ALL operator.
        
        Returns:
            bool: True if the rule contains more than one value and the operator is ALL; otherwise, False.
        """
        return len(self.apply_to.rule_values) > 1 and self.apply_to.operator == Operator.ALL


class ContainsRuleAndAnyConsideration(ConsiderRule[ContainsRule]):

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        """
        Determines if the given rule is a ContainsRule or NotContainsRule.
        
        Returns:
            bool: True if the rule is an instance of ContainsRule or NotContainsRule, otherwise False.
        """
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        """
        Initialize the consideration for (Not)ContainsRule with multiple values and the ANY operator, indicating that such a rule always evaluates to true.
        """
        super().__init__(apply_to, label='(Not) contains with ANY',
                         consideration='contains rule with more then one rule value and ANY is always TRUE')

    def apply(self) -> bool:
        """
        Return True if the rule has multiple values and uses the ANY operator.
        
        Returns:
            bool: True if the rule contains more than one value and the operator is ANY; otherwise, False.
        """
        return len(self.apply_to.rule_values) > 1 and self.apply_to.operator == Operator.ANY


class ContainsShortRuleValueConsideration(ConsiderRule[ContainsRule]):
    length_short = 4

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        """
        Determines if the given rule is a ContainsRule or NotContainsRule.
        
        Returns:
            bool: True if the rule is an instance of ContainsRule or NotContainsRule, otherwise False.
        """
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        """
        Initialize the consideration for contains rules with short values and the ANY operator.
        
        Parameters:
            apply_to (ContainsRule): The contains rule instance to which this consideration applies.
        """
        message = '\n'.join([f'Contains rule with short rule values [{self.__class__.length_short}] ',
                             f'and ANY can have many hits'])
        super().__init__(apply_to, label='contains rule length and operator',
                         consideration=message)

    def apply(self):
        """
        Checks if any rule value is shorter than the defined threshold and the operator is ANY.
        
        Returns:
            bool: True if at least one rule value is shorter than the class-defined minimum length and the operator is ANY; otherwise, False.
        """
        length_short = self.__class__.length_short
        if not any(len(value) < length_short for value in self.apply_to.rule_values):
            return False
        return self.apply_to.operator == Operator.ANY


class ContainsWithBeforeAndAfterConsideration(ConsiderRule[ContainsRule]):

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        """
        Determines if the given rule is a ContainsRule or NotContainsRule.
        
        Returns:
            bool: True if the rule is an instance of ContainsRule or NotContainsRule, otherwise False.
        """
        return isinstance(rule, (ContainsRule, NotContainsRule))

    def __init__(self, apply_to: ContainsRule):
        """
        Initialize a consideration for contains rules that return true without generating before and after values.
        """
        super().__init__(apply_to, label='contains with before and after',
                         consideration=f'Contains Rule return also TRUE without generating before and after values')

    def apply(self):
        """
        Checks if the rule's `add_before_or_after_values` attribute is set to True.
        
        Returns:
            bool: True if before or after values are added; otherwise, False.
        """
        return self.apply_to.add_before_or_after_values == True


# endregion


# region PATH OPERATIONS CONSIDERATIONS


class PathAndGreatLevelConsideration(ConsiderRule[IPathOperationRule]):
    max_levels = 4

    @classmethod
    def is_consideration(cls, rule: IFilterRule) -> bool:
        """
        Determines if the given rule is an instance of a path operation rule.
        
        Returns:
            bool: True if the rule implements IPathOperationRule, otherwise False.
        """
        return isinstance(rule, IPathOperationRule)

    def __init__(self, apply_to: IPathOperationRule):
        """
        Initialize a consideration for path operation rules with excessive maximum levels.
        
        Parameters:
            apply_to (IPathOperationRule): The path operation rule to evaluate.
        """
        message = '\n'.join([f'Many levels are slow  [greater then {self.__class__.max_levels}].',
                            'Does it REALLY need a dependency on files or folders deep in the file system'])
        super().__init__(apply_to, label='path rules and max_level',
                         consideration=message)

    def apply(self):
        """
        Checks if the rule's maximum level exceeds the allowed threshold.
        
        Returns:
            bool: True if the rule's max_level is greater than the class-defined max_levels; otherwise, False.
        """
        return self.apply_to.max_level > self.__class__.max_levels


# endregion


def _considerations() -> List[Type[ConsiderRule]]:
    """
    Collects and returns all consideration classes defined in the global scope.
    
    Returns:
        List of consideration class types that are subclasses of ConsiderRule and whose names end with 'Consideration'.
    """
    rules: List[Type[ConsiderRule]] = []
    for name, value in globals().items():
        if not name.endswith('Consideration'):
            continue
        if not issubclass(value, ConsiderRule):
            continue
        rules.append(value)
    return rules


def get_considerations(filter_rule: IFilterRule) -> List[ConsiderRule[IFilterRule]]:
    """
    Return a list of consideration objects applicable to the given filter rule.
    
    Each consideration analyzes the rule for potential issues or warnings based on its configuration.
    
    Parameters:
        filter_rule (IFilterRule): The filter rule to analyze.
    
    Returns:
        List[ConsiderRule[IFilterRule]]: A list of instantiated consideration objects relevant to the provided rule.
    """
    return [rule(filter_rule) for rule in _considerations()
            if rule.is_consideration(filter_rule)]
