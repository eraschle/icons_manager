from abc import abstractmethod
from typing import Any, Dict, Generic, List, Protocol, Sequence, Type, TypeVar

from icon_manager.interfaces.managers import (IAttributeRuleController,
                                              IConfigManager,
                                              IConfigRuleController,
                                              IRuleController)
from icon_manager.rules.base import IFilterRule, RuleProtocol
from icon_manager.rules.rules import (EqualsRule, IPathOperationRule,
                                      IRuleValuesFilter)
from icon_manager.validation.base.validations import (MinLengthRule,
                                                      MinValueRule)
from icon_manager.validation.base.validator import (IRuleViolation, IValidator,
                                                    ValidationRule, Validator)
from icon_manager.validation.considerations import get_considerations
from icon_manager.validation.validation_rules import (
    KnownOperatorRule, KnownRuleAttributeRule, PathOperationAttributeRule)


def get_rule_validation_rules(rule: IRuleValuesFilter) -> List[ValidationRule]:
    return [
        MinLengthRule(rule.rule_values, 'Rule Values', min_length=1),
        KnownOperatorRule(rule.operator, 'Operator'),
        KnownRuleAttributeRule(rule.attribute, 'RuleAttribute')
    ]


class FolderRuleValidator(Validator[IRuleValuesFilter]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        return isinstance(rule, IRuleValuesFilter)

    def get_validations(self) -> list:
        return [
            MinLengthRule(self.rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(self.rule.operator, 'Operator'),
            KnownRuleAttributeRule(self.rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        return get_considerations(self.rule)


class EqualsRuleValidator(Validator[EqualsRule]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        return isinstance(rule, EqualsRule)

    def get_validations(self) -> list:
        return [
            MinLengthRule(self.rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(self.rule.operator, 'Operator'),
            KnownRuleAttributeRule(self.rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        return get_considerations(self.rule)


class ContainsPathRuleValidator(Validator[IPathOperationRule]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        return isinstance(rule, IPathOperationRule)

    def get_validations(self) -> list:
        return [
            *get_rule_validation_rules(self.rule),
            MinValueRule(self.rule.max_level, 'max_level', min_value=1),
            PathOperationAttributeRule(self.rule.attribute, 'path_attribute',
                                       'Path operations only works with path attribute')
        ]

    def get_considerations(self) -> list:
        return get_considerations(self.rule)


def _validators() -> List[Type[Validator]]:
    rules: List[Type[Validator]] = []
    for name, value in globals().items():
        if not name.endswith('RuleValidator'):
            continue
        if not issubclass(value, Validator):
            continue
        rules.append(value)
    return rules


def get_filter_validators(filter_rule: IFilterRule) -> List[Validator]:
    return [validator(filter_rule) for validator in _validators()
            if validator.is_validator(filter_rule)]


class CheckerRuleViolations(IRuleViolation):

    def __init__(self, checker: IRuleController, results: Sequence[IRuleViolation]):
        self.checker = checker
        self.results = results

    @property
    def violations(self) -> Dict[str, Any]:
        violations = {}
        for result in self.results:
            if result.is_successful():
                continue
            violations.update(result.violations)
        return {self.checker.name: violations}

    @property
    def considers(self) -> Dict[str, Any]:
        considers = {}
        for result in self.results:
            if not result.any_considers():
                continue
            considers.update(result.considers)
        return {self.checker.name: considers}

    def is_successful(self) -> bool:
        return all(result.is_successful() for result in self.results)

    def any_considers(self) -> bool:
        return any(result.any_considers() for result in self.results)

    def __str__(self) -> str:
        return super().__str__()


TChecker = TypeVar('TChecker', bound=IRuleController)


class CheckerValidator(IValidator, Generic[TChecker]):

    @abstractmethod
    def get_validators(self) -> List[IValidator]:
        pass

    def analyze(self) -> IRuleViolation:
        results = []
        for validator in self.get_validators():
            results.append(validator.analyze())
        return self.get_rule_violation(results)

    @abstractmethod
    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        pass


class AttributeCheckerValidator(CheckerValidator[IAttributeRuleController]):

    def __init__(self, checker: IAttributeRuleController):
        self.controller = checker

    def get_validators(self) -> List[Validator]:
        validators = []
        for rule in self.controller.rules:
            rule_validators = get_filter_validators(rule)
            validators.extend(rule_validators)
        return validators

    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        return CheckerRuleViolations(self.controller, results)


class RuleCheckerValidator(Protocol):

    @property
    def name(self) -> str:
        ...

    @property
    def path(self) -> str:
        ...

    @property
    def violations(self) -> Dict[str, Any]:
        ...

    @property
    def considers(self) -> Dict[str, Any]:
        ...


class RuleManagerValidator(CheckerValidator[IConfigManager]):

    def __init__(self, controller: IConfigRuleController):
        self.controller = controller

    def get_validators(self) -> List[IValidator]:
        validators = []
        for controller in self.controller.controllers:
            validator = AttributeCheckerValidator(controller)
            validators.append(validator)
        return validators

    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        return CheckerRuleViolations(self.controller, results)
