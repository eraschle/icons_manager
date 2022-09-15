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
        ...

    def apply(self) -> bool:
        """
        Abstract method that must be implemented by concrete get_rules in order to return a boolean
        indicating whether the rule is respected or not.

        :return: True if the rule is respected, False otherwise
        :rtype: bool
        """
        ...

    def get_violation(self) -> str:
        """
        Returns the message that will be used by the validator if the rule is not respected.
        If a custom error message is provided during rule instantiation that one will be used,
        otherwise the default one.

        :return: Error message
        :rtype: str
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
        raise NotImplementedError

    #: Default error message for the rule (class attribute).
    default_consideration_message = 'Make this setting sense.'

    def __init__(self, apply_to: TRule, label: str = '',
                 consideration: Optional[str] = None):
        self.__apply_to = apply_to
        self.label = label
        self.consideration = consideration

    @property
    def apply_to(self) -> TRule:
        if isfunction(self.__apply_to):
            return self.__apply_to()
        return self.__apply_to

    def get_violation(self) -> str:
        return self.consideration or self.default_consideration_message

    @abstractmethod
    def apply(self) -> bool:
        pass  # pragma: no cover

    def __invert__(self):
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
        self.__apply_to = apply_to
        self.label = label
        self.custom_error_message = error_message
        self.stop_if_invalid = stop_if_invalid

    @property
    def apply_to(self) -> TValue:
        if isfunction(self.__apply_to):
            # noinspection PyCallingNonCallable
            return self.__apply_to()
        return self.__apply_to

    def get_violation(self) -> str:
        return self.custom_error_message or self.default_error_message

    @abstractmethod
    def apply(self) -> bool:
        pass  # pragma: no cover

    def __invert__(self):
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
        super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.rules = rules
        self._failed_rule = None

    def _get_configured_rule(self, entry):
        rule_config = {'apply_to': self.apply_to, 'label': self.label}
        rule_class = entry
        if isinstance(entry, (list, tuple)):
            if len(entry) != 2 or not issubclass(entry[0], ValidationRule) or not isinstance(entry[1], dict):
                msg = 'Provided rule configuration does not respect the format: ' \
                      '(rule_class: ValidationRule, rule_config: dict)'
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
        if isinstance(self._failed_rule, ValidationRule):
            return self._failed_rule.get_violation()
        return super().get_violation()

    def apply(self) -> bool:
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
        ...

    @property
    def considers(self) -> Dict[str, Any]:
        ...

    def is_successful(self) -> bool:
        ...

    def any_considers(self) -> bool:
        ...


class RuleViolations(IRuleViolation):
    """
    Represents a report of Validator's validate() call.

    :param errors: Map containing errors descriptions (if one ore more get_rules are not respected)
    :type errors: dict
    """

    def __init__(self, errors: Optional[Dict[str, Any]] = None,
                 considers: Optional[Dict[str, Any]] = None):
        self._errors = errors or {}
        self._considers = considers or {}

    @property
    def violations(self) -> Dict[str, Any]:
        return self._errors

    @property
    def considers(self) -> Dict[str, Any]:
        return self._considers

    def annotate_considers(self, rule: ConsiderRule) -> None:
        """
        Takes note of a rule validation failure by collecting its error message.

        :param rule: Rule that failed validation.
        :type rule: ValidationRule
        :return: None
        """
        if self.considers.get(rule.label) is None:
            self.considers[rule.label] = []
        self.considers[rule.label].append(rule.get_violation())

    def annotate_violation(self, rule: ValidationRule) -> None:
        """
        Takes note of a rule validation failure by collecting its error message.

        :param rule: Rule that failed validation.
        :type rule: ValidationRule
        :return: None
        """
        if self.violations.get(rule.label) is None:
            self.violations[rule.label] = []
        self.violations[rule.label].append(rule.get_violation())

    def annotate_exception(self, exception: Exception,
                           rule: Optional[ValidationRule] = None) -> None:
        """
        Takes note of an exception occurred during validation.
        (Typically caused by an invalid attribute/key access inside get_rules() method)

        :param exception: Exception catched during validate() phase.
        :type exception: Exception
        :param rule: Validation rule that has generated the exception.
        :type rule: ValidationRule
        :return: None
        """
        error_key = rule.label if isinstance(
            rule, ValidationRule) else 'get_rules'
        if self.violations.get(error_key) is None:
            self.violations[error_key] = []
        self.violations[error_key].append(str(exception))

    def is_successful(self) -> bool:
        """
        Checks that the validation result does not contain errors.

        :return: True if the validation is successful, False otherwise.
        :rtype: bool
        """
        return len(self.violations) == 0

    def any_considers(self) -> bool:
        """
        Checks that the validation result does not contain errors.

        :return: True if the validation is successful, False otherwise.
        :rtype: bool
        """
        return len(self.considers) > 0

    def __str__(self) -> str:
        return f'Violations: {len(self.violations)} Considers: {len(self.considers)}'

    def __repr__(self) -> str:
        return self.__str__()


class ValidationException(Exception):

    def __init__(self, validation_result: RuleViolations,
                 message: str = 'Data did not validate.'):
        super().__init__(message)
        self.message = message
        self.validation_result = validation_result

    def __str__(self):
        info = {'message': self.message,
                'errors': self.validation_result.violations}
        formatted_string = pprint.pformat(info)
        return formatted_string


class IValidator(Protocol):

    def analyze(self) -> IRuleViolation:
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
        raise NotImplementedError

    def __init__(self, rule: TRule):
        self.rule = rule

    def __enter__(self):
        validation = self.analyze()
        if not validation.is_successful():
            raise ValidationException(validation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def analyze(self) -> RuleViolations:
        result = self.validate(RuleViolations())
        return self.consider(result)

    @abstractmethod
    def get_validations(self) -> Iterable[ValidationRule]:
        pass  # pragma: no cover

    def validate(self, result: RuleViolations) -> RuleViolations:
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
        pass  # pragma: no cover

    def consider(self, result: RuleViolations) -> RuleViolations:
        for rule in self.get_considerations():
            if not rule.apply():
                continue
            result.annotate_considers(rule)
        return result
