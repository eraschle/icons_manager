import pprint
from abc import ABC, abstractmethod
from enum import Enum
from inspect import isfunction
from typing import Any, Dict, Generic, Iterable, Optional, Protocol, TypeVar

from icon_manager.rules.base import RuleProtocol


class JoinType(Enum):
    AND = 1
    OR = 2
    XOR = 3
    NOT = 4


TValue = TypeVar('TValue', bound=object, covariant=True)


class IValidatorRule(Protocol, Generic[TValue]):

    @property
    def apply_to(self) -> TValue:
        """
        Returns the value or object that this rule will validate.
        """
        ...

    def apply(self) -> bool:
        """
        Determine whether the rule is satisfied.
        
        Returns:
            bool: True if the rule passes, False otherwise.
        """
        ...

    def get_violation(self) -> str:
        """
        Return the error message associated with this rule if it fails.
        
        If a custom error message was provided during instantiation, it is returned; otherwise, the default message is used.
        
        Returns:
            str: The error message for this rule.
        """
        ...


TRule = TypeVar('TRule', bound=RuleProtocol)


class ConsiderRule(IValidatorRule[TRule]):
    """
    Base abstract rule class from which concrete ones must inherit from.

    :param apply_to: The against which the rule is applied (TRule).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    @classmethod
    def is_consideration(cls, rule: RuleProtocol) -> bool:
        """
        Raises NotImplementedError to indicate that subclasses must implement logic to determine if a rule is a consideration rule.
        
        Parameters:
            rule: The rule instance to check.
        
        Returns:
            bool: True if the rule is a consideration rule; otherwise, False.
        """
        raise NotImplementedError

    #: Default error message for the rule (class attribute).
    default_consideration_message = 'Make this setting sense.'

    def __init__(self, apply_to: TRule, label: str = '',
                 consideration: Optional[str] = None):
        """
                 Initialize a consideration rule with the target object, label, and optional consideration message.
                 
                 Parameters:
                     apply_to (TRule): The object or value to which the rule will be applied.
                     label (str, optional): A descriptive label for the rule or field. Defaults to an empty string.
                     consideration (str, optional): Custom message to use if the rule is considered. Defaults to None.
                 """
                 self.__apply_to = apply_to
        self.label = label
        self.consideration = consideration

    @property
    def apply_to(self) -> TRule:
        """
        Returns the value to which the rule should be applied, calling it if it is a function.
        
        Returns:
            The target value or the result of calling the target if it is a function.
        """
        if isfunction(self.__apply_to):
            return self.__apply_to()
        return self.__apply_to

    def get_violation(self) -> str:
        """
        Return the consideration message for this rule.
        
        If a custom consideration message is set, it is returned; otherwise, the default message is used.
        """
        return self.consideration or self.default_consideration_message

    @abstractmethod
    def apply(self) -> bool:
        """
        Evaluates the rule and returns True if the rule passes, otherwise False.
        
        This method must be implemented by subclasses to define the specific validation or consideration logic.
        """
        pass  # pragma: no cover

    def __invert__(self):
        """
        Inverts the logic of the rule's `apply` method, causing it to return the opposite boolean result on subsequent calls.
        
        Returns:
            self: The rule instance with inverted logic.
        """
        def inverted_apply(apply):
            def decorated_function():
                return not apply()

            return decorated_function

        self.apply = inverted_apply(self.apply)
        return self


class ValidationRule(IValidatorRule[TValue]):
    """
    Base abstract rule class from which concrete ones must inherit from.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule (class attribute).
    default_error_message = 'Data is invalid.'

    def __init__(self, apply_to: TValue, label: str, error_message: Optional[str] = None,
                 stop_if_invalid: bool = False):
        """
                 Initialize a validation rule with the target value, label, optional custom error message, and stop-on-failure flag.
                 
                 Parameters:
                     apply_to: The value or callable to be validated.
                     label (str): A descriptive label for the rule, typically indicating the field or property being validated.
                     error_message (Optional[str]): Custom error message to use if the rule fails.
                     stop_if_invalid (bool): If True, validation will halt upon this rule's failure.
                 """
                 self.__apply_to = apply_to
        self.label = label
        self.custom_error_message = error_message
        self.stop_if_invalid = stop_if_invalid

    @property
    def apply_to(self) -> TValue:
        """
        Returns the value to which the rule should be applied, calling it if it is a function.
        
        Returns:
            The value or the result of calling the value if it is a function.
        """
        if isfunction(self.__apply_to):
            # noinspection PyCallingNonCallable
            return self.__apply_to()
        return self.__apply_to

    def get_violation(self) -> str:
        """
        Return the error message for this validation rule, using the custom message if provided, otherwise the default message.
        """
        return self.custom_error_message or self.default_error_message

    @abstractmethod
    def apply(self) -> bool:
        """
        Evaluates the rule and returns True if the rule passes, otherwise False.
        
        This method must be implemented by subclasses to define the specific validation or consideration logic.
        """
        pass  # pragma: no cover

    def __invert__(self):
        """
        Inverts the logic of the rule's `apply` method, causing it to return the opposite boolean result on subsequent calls.
        
        Returns:
            self: The rule instance with inverted logic.
        """
        def inverted_apply(apply):
            def decorated_function():
                return not apply()

            return decorated_function

        self.apply = inverted_apply(self.apply)
        return self


class InvalidRuleGroupException(Exception):
    """
    Exception raised by RuleGroup if the provided configuration is invalid.
    """

    def __init__(self, message: str):
        """
        Initialize the exception with a custom error message.
        
        Parameters:
            message (str): The error message describing the exception.
        """
        self.message = message
        super().__init__(message)


class RuleGroup(ValidationRule):
    """
    Allows the execution of multiple rules sequentially.

    :Example:

    >>> rules = [
    >>>    (TypeRule, {'valid_type': list}),
    >>>    (MinLengthRule, {'min_length': 1}),
    >>>    UniqueItemsRule
    >>> ]
    >>> group = RuleGroup(apply_to=countries, label='Countries', rules=rules)

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param rules: List of rules to execute. The list can contain rule type (ie: FullStringRule, MinValueRule...) or \
    tuples in the format: "(RuleClass, options)" (ie: "(MinLengthRule, {'min_length': 1})")
    :type rules: list
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    def __init__(self, apply_to: object, label: str, rules: list,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a RuleGroup with a target value, label, and a sequence of validation rules.
                 
                 Parameters:
                     apply_to (object): The value or object to be validated by the rule group.
                     label (str): A descriptive label for the rule group.
                     rules (list): A list of validation rule classes or (rule class, config dict) tuples to be applied in sequence.
                     error_message (Optional[str]): Custom error message for the group if validation fails.
                     stop_if_invalid (bool): If True, stops evaluating further rules after the first failure.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.rules = rules
        self._failed_rule = None

    def _get_configured_rule(self, entry):
        """
        Instantiate and configure a validation rule from a class or a (class, config) tuple.
        
        Parameters:
        	entry: Either a ValidationRule subclass or a tuple of (ValidationRule subclass, configuration dict).
        
        Returns:
        	ValidationRule: An instance of the specified rule class, configured with the provided parameters.
        
        Raises:
        	InvalidRuleGroupException: If the entry is not a valid rule class or configuration tuple.
        """
        rule_config = {'apply_to': self.apply_to, 'label': self.label}
        rule_class = entry
        if isinstance(entry, (list, tuple)):
            if len(entry) != 2 or not issubclass(entry[0], ValidationRule) or not isinstance(entry[1], dict):
                msg = 'Provided rule configuration does not respect the format: (rule_class: ValidationRule, rule_config: dict)'
                raise InvalidRuleGroupException(msg)
            rule_class = entry[0]
            rule_config.update(entry[1])
        elif entry is None or not issubclass(entry, ValidationRule):
            msg = 'Expected type "ValidationRule", got "{}" instead.'.format(
                str(entry))
            raise InvalidRuleGroupException(msg)
        rule = rule_class(**rule_config)  # type: ValidationRule
        return rule

    def get_error_message(self) -> str:
        """
        Return the error message from the first failed rule in the group, or the default violation message if no rule has failed.
        """
        if isinstance(self._failed_rule, ValidationRule):
            return self._failed_rule.get_violation()
        return super().get_violation()

    def apply(self) -> bool:
        """
        Executes each rule in the group sequentially, returning False on the first failure or exception.
        
        Returns:
            bool: True if all rules pass without exception; False if any rule fails or raises an exception.
        """
        for entry in self.rules:
            rule = self._get_configured_rule(entry)
            try:
                if not rule.apply():
                    self._failed_rule = rule
                    return False
            except Exception:
                self._failed_rule = rule
                return False
        return True


class IRuleViolation(Protocol):

    @property
    def violations(self) -> Dict[str, Any]:
        """
        Returns a dictionary of validation errors collected during rule evaluation.
        
        Returns:
            Dict[str, Any]: A mapping of rule labels to their corresponding error messages.
        """
        ...

    @property
    def considers(self) -> Dict[str, Any]:
        """
        Returns a dictionary of consideration messages collected during validation, keyed by rule label.
        """
        ...

    def is_successful(self) -> bool:
        """
        Return True if there are no validation violations.
        
        Returns:
            bool: True if the validation result contains no errors; otherwise, False.
        """
        ...

    def any_considers(self) -> bool:
        """
        Return True if any consideration messages are present in the result.
        
        Returns:
            bool: True if there are any considerations, False otherwise.
        """
        ...


class RuleViolations(IRuleViolation):
    """
    Represents a report of Validator's validate() call.

    :param errors: Map containing errors descriptions (if one ore more get_rules are not respected)
    :type errors: dict
    """

    def __init__(self, errors: Optional[Dict[str, Any]] = None,
                 considers: Optional[Dict[str, Any]] = None):
        """
                 Initialize a RuleViolations instance with optional errors and considerations.
                 
                 Parameters:
                     errors (Optional[Dict[str, Any]]): Initial dictionary of validation errors.
                     considers (Optional[Dict[str, Any]]): Initial dictionary of consideration messages.
                 """
                 self._errors = errors or {}
        self._considers = considers or {}

    @property
    def violations(self) -> Dict[str, Any]:
        """
        Returns the dictionary of validation errors collected during rule evaluation.
        
        Returns:
            Dict[str, Any]: A mapping of rule labels to their corresponding error messages.
        """
        return self._errors

    @property
    def considers(self) -> Dict[str, Any]:
        """
        Returns the dictionary of consideration messages collected during validation.
        
        Returns:
            Dict[str, Any]: A mapping of rule labels to their corresponding consideration messages.
        """
        return self._considers

    def annotate_considers(self, rule: ConsiderRule) -> None:
        """
        Add a consideration message for a given consideration rule to the result set.
        
        Parameters:
            rule (ConsiderRule): The consideration rule whose message should be recorded.
        """
        if self.considers.get(rule.label) is None:
            self.considers[rule.label] = []
        self.considers[rule.label].append(rule.get_violation())

    def annotate_violation(self, rule: ValidationRule) -> None:
        """
        Record a validation failure by adding the rule's error message to the violations dictionary.
        
        Parameters:
            rule (ValidationRule): The validation rule that failed.
        """
        if self.violations.get(rule.label) is None:
            self.violations[rule.label] = []
        self.violations[rule.label].append(rule.get_violation())

    def annotate_exception(self, exception: Exception,
                           rule: Optional[ValidationRule] = None) -> None:
        """
                           Record an exception that occurred during validation, associating it with the relevant rule or the 'get_rules' key if no rule is provided.
                           
                           Parameters:
                               exception (Exception): The exception encountered during validation.
                               rule (Optional[ValidationRule]): The validation rule that triggered the exception, if applicable.
                           """
        error_key = rule.label if isinstance(
            rule, ValidationRule) else 'get_rules'
        if self.violations.get(error_key) is None:
            self.violations[error_key] = []
        self.violations[error_key].append(str(exception))

    def is_successful(self) -> bool:
        """
        Return True if there are no validation errors.
        
        Returns:
            bool: True if no violations exist; False otherwise.
        """
        return len(self.violations) == 0

    def any_considers(self) -> bool:
        """
        Return True if any consideration messages are present in the validation result.
        
        Returns:
            bool: True if there is at least one consideration message; False otherwise.
        """
        return len(self.considers) > 0

    def __str__(self) -> str:
        """
        Return a summary string indicating the number of violations and considerations recorded.
        """
        return f'Violations: {len(self.violations)} Considers: {len(self.considers)}'

    def __repr__(self) -> str:
        """
        Return a string representation of the object for debugging purposes.
        """
        return self.__str__()


class ValidationException(Exception):

    def __init__(self, validation_result: RuleViolations,
                 message: str = 'Data did not validate.'):
        """
                 Initialize a ValidationException with the given validation result and message.
                 
                 Parameters:
                     validation_result (RuleViolations): The result of the validation containing errors and considerations.
                     message (str): Optional custom error message to describe the validation failure.
                 """
                 super().__init__(message)
        self.message = message
        self.validation_result = validation_result

    def __str__(self):
        """
        Return a formatted string representation of the validation exception, including the message and associated errors.
        """
        info = {'message': self.message,
                'errors': self.validation_result.violations}
        formatted_string = pprint.pformat(info)
        return formatted_string


class IValidator(Protocol):

    def analyze(self) -> IRuleViolation:
        """
        Runs all validation and consideration rules and returns the aggregated validation results.
        
        Returns:
            IRuleViolation: An object containing any violations and considerations found during validation.
        """
        ...


class Validator(ABC, IValidator, Generic[TRule]):
    """
    Validate a rule model against a list of ValidationRule(s).
    This class is abstract, concrete validators must inherit from Validator in order to provide a
    an actual implementation of get_rules().

    :param rule: Data model to validate (like a dict or a custom Python TRule instance).
    :type rule: TRule
    """

    @classmethod
    def is_validator(cls, rule: RuleProtocol) -> bool:
        """
        Determine whether the given rule object is compatible with this validator class.
        
        This method must be implemented by subclasses to check if the provided rule can be validated by this validator type.
        
        Parameters:
            rule: The rule object to check for compatibility.
        
        Returns:
            True if the rule is supported by this validator class, otherwise False.
        """
        raise NotImplementedError

    def __init__(self, rule: TRule):
        """
        Initialize the Validator with the rule object to be validated.
        
        Parameters:
            rule (TRule): The object or data to be validated by this Validator instance.
        """
        self.rule = rule

    def __enter__(self):
        """
        Enters the validator context, performing validation and raising an exception if validation fails.
        
        Returns:
            self: The validator instance if validation is successful.
        
        Raises:
            ValidationException: If any validation rule fails.
        """
        validation = self.analyze()
        if not validation.is_successful():
            raise ValidationException(validation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the validator context manager without performing any additional actions.
        """
        pass

    def analyze(self) -> RuleViolations:
        """
        Runs all validation and consideration rules, returning the combined validation results.
        
        Returns:
            RuleViolations: The result containing any violations and considerations found during validation.
        """
        result = self.validate(RuleViolations())
        return self.consider(result)

    @abstractmethod
    def get_validations(self) -> Iterable[ValidationRule]:
        """
        Return an iterable of validation rules to be applied by the validator.
        
        This method must be implemented by subclasses to provide the set of strict validation rules relevant for the target object.
        """
        pass  # pragma: no cover

    def validate(self, result: RuleViolations) -> RuleViolations:
        """
        Applies all validation rules to the target object and records any violations or exceptions.
        
        Each validation rule is executed in sequence. If a rule fails, its violation is annotated in the result. If a rule is configured to stop on failure, subsequent rules are not executed. Any exceptions raised during rule evaluation are also recorded in the result.
        
        Parameters:
            result (RuleViolations): The object used to collect validation errors and exceptions.
        
        Returns:
            RuleViolations: The updated result containing all recorded violations and exceptions.
        """
        try:
            for validation in self.get_validations():
                try:
                    if validation.apply():
                        continue
                    result.annotate_violation(validation)
                    if validation.stop_if_invalid:
                        break
                except Exception as e:
                    result.annotate_exception(e, validation)
        except Exception as e:
            result.annotate_exception(e, None)
        return result

    @abstractmethod
    def get_considerations(self) -> Iterable[ConsiderRule]:
        """
        Return an iterable of consideration rules to be applied during validation.
        
        This method should be implemented by subclasses to provide the set of `ConsiderRule` instances that represent non-critical recommendations or warnings for the validation process.
        """
        pass  # pragma: no cover

    def consider(self, result: RuleViolations) -> RuleViolations:
        """
        Applies all consideration rules and annotates the result with any considerations that pass.
        
        Parameters:
        	result (RuleViolations): The current validation result to annotate.
        
        Returns:
        	RuleViolations: The updated result including any new considerations.
        """
        for rule in self.get_considerations():
            if not rule.apply():
                continue
            result.annotate_considers(rule)
        return result
