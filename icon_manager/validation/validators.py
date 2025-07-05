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
    """
    Return a list of validation rules for a rule implementing `IRuleValuesFilter`.
    
    The returned rules check that the rule values list is not empty, the operator is recognized, and the attribute is valid.
    """
    return [
        MinLengthRule(rule.rule_values, 'Rule Values', min_length=1),
        KnownOperatorRule(rule.operator, 'Operator'),
        KnownRuleAttributeRule(rule.attribute, 'RuleAttribute')
    ]


class FolderRuleValidator(Validator[IRuleValuesFilter]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        """
        Determine if the given rule is an instance of IRuleValuesFilter.
        
        Returns:
            bool: True if the rule implements IRuleValuesFilter, otherwise False.
        """
        return isinstance(rule, IRuleValuesFilter)

    def get_validations(self) -> list:
        """
        Return a list of validation rules for the associated rule, including checks for minimum rule values length, known operator, and known attribute.
        """
        return [
            MinLengthRule(self.rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(self.rule.operator, 'Operator'),
            KnownRuleAttributeRule(self.rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        """
        Return a list of considerations associated with the current rule.
        
        Returns:
            list: Considerations relevant to the rule being validated.
        """
        return get_considerations(self.rule)


class EqualsRuleValidator(Validator[EqualsRule]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        """
        Determine if the given rule is an instance of EqualsRule.
        
        Returns:
            bool: True if the rule is an EqualsRule, otherwise False.
        """
        return isinstance(rule, EqualsRule)

    def get_validations(self) -> list:
        """
        Return a list of validation rules for the associated rule, including checks for minimum rule values length, known operator, and known attribute.
        """
        return [
            MinLengthRule(self.rule.rule_values, 'Rule Values', min_length=1),
            KnownOperatorRule(self.rule.operator, 'Operator'),
            KnownRuleAttributeRule(self.rule.attribute, 'RuleAttribute')
        ]

    def get_considerations(self) -> list:
        """
        Return a list of considerations associated with the current rule.
        
        Returns:
            list: Considerations relevant to the rule being validated.
        """
        return get_considerations(self.rule)


class ContainsPathRuleValidator(Validator[IPathOperationRule]):

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        """
        Determine if the given rule is an instance of IPathOperationRule.
        
        Returns:
            bool: True if the rule implements IPathOperationRule, otherwise False.
        """
        return isinstance(rule, IPathOperationRule)

    def get_validations(self) -> list:
        """
        Return a list of validation rules for a path operation rule, including standard rule validations, a minimum value check for `max_level`, and a path attribute validation.
        """
        return [
            *get_rule_validation_rules(self.rule),
            MinValueRule(self.rule.max_level, 'max_level', min_value=1),
            PathOperationAttributeRule(self.rule.attribute, 'path_attribute',
                                       'Path operations only works with path attribute')
        ]

    def get_considerations(self) -> list:
        """
        Return a list of considerations associated with the current rule.
        
        Returns:
            list: Considerations relevant to the rule being validated.
        """
        return get_considerations(self.rule)


def _validators() -> List[Type[Validator]]:
    """
    Dynamically collects and returns all Validator subclasses in the global scope whose names end with 'RuleValidator'.
    
    Returns:
        List of Validator subclasses matching the naming convention.
    """
    rules: List[Type[Validator]] = []
    for name, value in globals().items():
        if not name.endswith('RuleValidator'):
            continue
        if not issubclass(value, Validator):
            continue
        rules.append(value)
    return rules


def get_filter_validators(filter_rule: IFilterRule) -> List[Validator]:
    """
    Return a list of validator instances applicable to the given filter rule.
    
    Each validator is instantiated for the provided filter rule if its `is_validator` class method returns True.
    Returns:
        List of Validator instances suitable for the filter rule.
    """
    return [validator(filter_rule) for validator in _validators()
            if validator.is_validator(filter_rule)]


class CheckerRuleViolations(IRuleViolation):

    def __init__(self, checker: IRuleController, results: Sequence[IRuleViolation]):
        """
        Initialize a CheckerRuleViolations instance with a rule controller and its validation results.
        
        Parameters:
            checker (IRuleController): The rule controller associated with these violations.
            results (Sequence[IRuleViolation]): The sequence of validation results to aggregate.
        """
        self.checker = checker
        self.results = results

    @property
    def violations(self) -> Dict[str, Any]:
        """
        Aggregate and return all violations from unsuccessful validation results, keyed by the checker's name.
        
        Returns:
            A dictionary mapping the checker's name to a merged dictionary of violations from all results that are not successful.
        """
        violations = {}
        for result in self.results:
            if result.is_successful():
                continue
            violations.update(result.violations)
        return {self.checker.name: violations}

    @property
    def considers(self) -> Dict[str, Any]:
        """
        Aggregate and return all considerations from validation results, grouped under the checker's name.
        
        Returns:
            dict: A dictionary with the checker's name as the key and a merged dictionary of all considerations from results that have any considerations.
        """
        considers = {}
        for result in self.results:
            if not result.any_considers():
                continue
            considers.update(result.considers)
        return {self.checker.name: considers}

    def is_successful(self) -> bool:
        """
        Return True if all aggregated validation results are successful.
        """
        return all(result.is_successful() for result in self.results)

    def any_considers(self) -> bool:
        """
        Return True if any contained validation result has considerations.
        """
        return any(result.any_considers() for result in self.results)

    def __str__(self) -> str:
        """
        Return the string representation of the object using the base class implementation.
        """
        return super().__str__()


TChecker = TypeVar('TChecker', bound=IRuleController)


class CheckerValidator(IValidator, Generic[TChecker]):

    @abstractmethod
    def get_validators(self) -> List[IValidator]:
        """
        Returns a list of validator instances applicable to the rules or controllers managed by this checker.
        
        This method should be implemented by subclasses to provide the specific validators needed for the contained rules or controllers.
        """
        pass

    def analyze(self) -> IRuleViolation:
        """
        Runs analysis on all validators returned by `get_validators()` and aggregates their results into a single rule violation.
        
        Returns:
            IRuleViolation: The aggregated violation result from all contained validators.
        """
        results = []
        for validator in self.get_validators():
            results.append(validator.analyze())
        return self.get_rule_violation(results)

    @abstractmethod
    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        """
        Aggregate a sequence of rule violation results into a single CheckerRuleViolations instance for the associated checker.
        
        Parameters:
            results (Sequence[IRuleViolation]): The list of rule violation results to aggregate.
        
        Returns:
            CheckerRuleViolations: An aggregated violation result for the checker.
        """
        pass


class AttributeCheckerValidator(CheckerValidator[IAttributeRuleController]):

    def __init__(self, checker: IAttributeRuleController):
        """
        Initialize the validator with the given attribute rule controller.
        
        Parameters:
            checker (IAttributeRuleController): The attribute rule controller to be validated.
        """
        self.controller = checker

    def get_validators(self) -> List[Validator]:
        """
        Return a list of validator instances applicable to each rule in the controller.
        
        Iterates through all rules managed by the controller, collects their corresponding filter validators, and returns the combined list.
        """
        validators = []
        for rule in self.controller.rules:
            rule_validators = get_filter_validators(rule)
            validators.extend(rule_validators)
        return validators

    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        """
        Aggregate multiple rule violation results for the controller into a CheckerRuleViolations instance.
        
        Parameters:
            results (Sequence[IRuleViolation]): The sequence of rule violation results to aggregate.
        
        Returns:
            CheckerRuleViolations: An aggregated result representing all violations for the controller.
        """
        return CheckerRuleViolations(self.controller, results)


class RuleCheckerValidator(Protocol):

    @property
    def name(self) -> str:
        """
        Returns the name of the rule checker or validator.
        """
        ...

    @property
    def path(self) -> str:
        """
        Returns the path associated with the rule checker.
        
        This property typically represents the hierarchical or logical location of the rule checker within the configuration or validation structure.
        
        Returns:
            str: The path of the rule checker.
        """
        ...

    @property
    def violations(self) -> Dict[str, Any]:
        """
        Return a dictionary mapping the checker's name to a merged dictionary of all violations from unsuccessful validation results.
        
        Returns:
            A dictionary where the key is the checker's name and the value is a combined dictionary of violations from all failed validations.
        """
        ...

    @property
    def considers(self) -> Dict[str, Any]:
        """
        Return a dictionary mapping the checker's name to merged considerations from all validation results that contain considerations.
        """
        ...


class RuleManagerValidator(CheckerValidator[IConfigManager]):

    def __init__(self, controller: IConfigRuleController):
        """
        Initialize the RuleManagerValidator with the given configuration rule controller.
        
        Parameters:
            controller (IConfigRuleController): The configuration rule controller to be validated.
        """
        self.controller = controller

    def get_validators(self) -> List[IValidator]:
        """
        Returns a list of attribute checker validators for each controller managed by this configuration controller.
        
        Each validator corresponds to an attribute rule controller contained within the configuration controller.
        """
        validators = []
        for controller in self.controller.controllers:
            validator = AttributeCheckerValidator(controller)
            validators.append(validator)
        return validators

    def get_rule_violation(self, results: Sequence[IRuleViolation]) -> CheckerRuleViolations:
        """
        Aggregate multiple rule violation results for the controller into a CheckerRuleViolations instance.
        
        Parameters:
            results (Sequence[IRuleViolation]): The sequence of rule violation results to aggregate.
        
        Returns:
            CheckerRuleViolations: An aggregated result representing all violations for the controller.
        """
        return CheckerRuleViolations(self.controller, results)
