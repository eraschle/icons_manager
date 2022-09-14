from typing import List

from icon_manager.rules.rules import EqualsRule, IPathOperationRule, IRuleValuesFilter
from icon_manager.validation.validation_rules import (KnownOperatorRule,
                                                      KnownRuleAttributeRule)
from icon_manager.validation.base.validations import (MinLengthRule,
                                                      MinValueRule)
from icon_manager.validation.base.validator import ValidationRule, Validator


def get_rule_values_validation_rules(rule: IRuleValuesFilter) -> List[ValidationRule]:
    return [
        MinLengthRule(rule.rule_values, 'Rule Values', min_length=1),
        KnownOperatorRule(rule.operator, 'Operator'),
        KnownRuleAttributeRule(rule.attribute, 'RuleAttribute')
    ]


class FolderRuleValidator(Validator[IRuleValuesFilter]):
    def get_validations(self) -> list:
        rule = self.data
        return [
            MinLengthRule(rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(rule.operator, 'Operator'),
            KnownRuleAttributeRule(rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        return []


class EqualsRuleValidator(Validator[EqualsRule]):
    def get_validations(self) -> list:
        rule = self.data
        return [
            MinLengthRule(rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(rule.operator, 'Operator'),
            KnownRuleAttributeRule(rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        return []


class ContainsPathRuleValidator(Validator[IPathOperationRule]):
    def get_validations(self) -> list:
        rule = self.data
        return [
            *get_rule_values_validation_rules(rule),
            MinValueRule(rule.max_level, 'max_level', min_value=1)
        ]

    def get_considerations(self) -> list:
        return []
