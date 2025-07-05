import re
from datetime import datetime
from typing import Collection, Optional, Union

from icon_manager.validation.base.validator import TValue
from icon_manager.validation.validation_rules import ValidationRule

DATA_ERRORS = (TypeError, IndexError, KeyError,
               NameError, ValueError, AttributeError)


class TypeRule(ValidationRule[object]):
    """
    Ensure that the target value is an instance of the given type.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param valid_type: Valid class
    :type valid_type: type
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Object is not an instance of the expected type.'

    def __init__(self, apply_to: object, label: str, valid_type: type,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a type validation rule to check if a value is an instance of a specified type.
                 
                 Parameters:
                     apply_to (object): The value to validate.
                     label (str): A descriptive label for the value being validated.
                     valid_type (type): The expected type for validation.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.valid_type = valid_type

    def apply(self) -> bool:
        """
        Return True if the target value is an instance of the specified type.
        
        Returns:
            bool: True if the value to validate is an instance of the required type; otherwise, False.
        """
        return isinstance(self.apply_to, self.valid_type)


class FullStringRule(ValidationRule[str]):
    """
    Ensure that the target value is a non empty string object.

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

    #: Default error message for the rule.
    default_error_message = 'String is empty.'

    def __init__(self, apply_to: str, label: str,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule with the target value, label, optional error message, and a flag to stop further validation if invalid.
                 
                 Parameters:
                     apply_to (str): The value to be validated.
                     label (str): A descriptive label for the field being validated.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): If True, halts further validation when this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)

    def apply(self):
        """
        Check if the target value is a non-empty string after stripping whitespace.
        
        Returns:
            bool: True if the value is a string with non-zero length after stripping, otherwise False.
        """
        value = self.apply_to  # type: str
        return isinstance(value, str) and len(value.strip()) > 0


class ChoiceRule(ValidationRule[TValue]):
    """
    Ensure that the target value is contained in a provided list of possible options.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param choices: Available options.
    :type choices: tuple
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value not found in available choices.'

    def __init__(self, apply_to: TValue, label: str, choices: tuple,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a value is among a set of allowed choices.
                 
                 Parameters:
                     apply_to: The value to validate.
                     label: A descriptive label for the field being validated.
                     choices: A tuple containing the valid options for the value.
                     error_message: Optional custom error message to use if validation fails.
                     stop_if_invalid: If True, halts further validation when this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.choices = choices

    def apply(self) -> bool:
        """
        Return True if the target value is contained within the allowed choices.
        
        Returns:
            bool: True if the value is in the choices tuple; False if not or if a data error occurs.
        """
        try:
            return self.apply_to in self.choices
        except DATA_ERRORS:
            return False


Number = Union[int, float]


class MinValueRule(ValidationRule[float]):
    """
    Ensure that the target value is >= than the provided reference value.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param min_value: Minimum value allowed.
    :type min_value: float
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value is smaller than expected one.'

    def __init__(self, apply_to: Number, label: str, min_value: float,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a numeric value is greater than or equal to a specified minimum.
                 
                 Parameters:
                     apply_to (Number): The numeric value to validate.
                     label (str): A descriptive label for the value being validated.
                     min_value (float): The minimum allowed value for validation.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.min_value = min_value

    def apply(self) -> bool:
        """
        Return True if the target value is greater than or equal to the specified minimum value.
        
        Returns:
            bool: True if the value meets or exceeds the minimum; False if not or if a data error occurs.
        """
        try:
            return self.apply_to >= self.min_value
        except DATA_ERRORS:
            return False


class MaxValueRule(ValidationRule[Number]):
    """
    Ensure that the target value is <= than the provided reference value.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param max_value: Maximum value allowed.
    :type max_value: float
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value is greater than expected one.'

    def __init__(self, apply_to: Number, label: str, max_value: float,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a numeric value is less than or equal to a specified maximum.
                 
                 Parameters:
                     apply_to (Number): The numeric value to validate.
                     label (str): A descriptive label for the value being validated.
                     max_value (float): The maximum allowed value for validation.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.max_value = max_value

    def apply(self) -> bool:
        """
        Return True if the target value is less than or equal to the specified maximum value.
        
        Returns:
            bool: True if the value is less than or equal to the maximum; False if not or if a data error occurs.
        """
        try:
            return self.apply_to <= self.max_value
        except DATA_ERRORS:
            return False


LengthValue = Union[str, list, tuple, set, dict, Collection]


class MinLengthRule(ValidationRule[LengthValue]):
    """
    Ensure that the target value has a length >= than the provided reference value.
    This rule can be applied to all python objects supporting len() (strings, lists, tuples, sets, dicts... and even
    custom types).

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param min_length: Minimum length allowed.
    :type min_length: int
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Length is smaller than expected one.'

    def __init__(self, apply_to: LengthValue, label: str, min_length: int,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a rule that validates whether a value's length is greater than or equal to a specified minimum.
                 
                 Parameters:
                     apply_to: The value whose length will be validated.
                     label: A descriptive label for the field being validated.
                     min_length: The minimum allowed length for the value.
                     error_message: Optional custom error message to use if validation fails.
                     stop_if_invalid: If True, stops further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.min_length = min_length

    def apply(self) -> bool:
        """
        Return True if the target value has a length greater than or equal to the specified minimum length.
        
        Returns:
            bool: True if the value's length is at least the minimum; False if not or if a data error occurs.
        """
        try:
            # noinspection PyTypeChecker
            return len(self.apply_to) >= self.min_length
        except DATA_ERRORS:
            return False


class MaxLengthRule(ValidationRule[LengthValue]):
    """
    Ensure that the target value has a length <= than the provided reference value.
    This rule can be applied to all python objects supporting len() (strings, lists, tuples, sets, dicts... and even
    custom types).

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param max_length: Maximum length allowed.
    :type max_length: int
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Length is greater than expected one.'

    def __init__(self, apply_to: LengthValue, label: str, max_length: int,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a rule that validates whether a value's length does not exceed a specified maximum.
                 
                 Parameters:
                     apply_to: The value whose length will be validated.
                     label: A descriptive label for the field being validated.
                     max_length: The maximum allowed length for the value.
                     error_message: Optional custom error message to use if validation fails.
                     stop_if_invalid: If True, stops further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.max_length = max_length

    def apply(self) -> bool:
        """
        Return True if the target value's length is less than or equal to the specified maximum length.
        
        Returns:
            bool: True if the value's length does not exceed the maximum; False if it exceeds or if a data error occurs.
        """
        try:
            # noinspection PyTypeChecker
            return len(self.apply_to) <= self.max_length
        except DATA_ERRORS:
            return False


class RangeRule(ValidationRule[TValue]):
    """
    Ensure that the target value is contained in the provided range.

    **IMPORTANT**: this rule handles python range() objects (and its "step" configuration),
    so does not support floats as test value
    (testing for a float will always fail and even for an integer if it doesn't match the step increment).

    For a validation like "value *BETWEEN* x *AND* y" use **IntervalRule** instead!

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param valid_range: Allowed range.
    :type valid_range: range
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value is out of range.'

    def __init__(self, apply_to: TValue, label: str, valid_range: range,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a value is contained within a specified Python range.
                 
                 Parameters:
                     apply_to: The value to validate.
                     label: A descriptive label for the field being validated.
                     valid_range: The Python `range` object defining valid values.
                     error_message: Optional custom error message to use if validation fails.
                     stop_if_invalid: If True, stops further validation when this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.valid_range = valid_range

    def apply(self) -> bool:
        """
        Return True if the target value is contained within the specified Python range.
        
        Returns:
            bool: True if the value is in the range; False if not or if a data error occurs.
        """
        try:
            return self.apply_to in self.valid_range
        except DATA_ERRORS:
            return False


class IntervalRule(ValidationRule[Number]):
    """
    Ensure that the target value is contained in the provided interval.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param interval_from: Minimum allowed value.
    :type interval_from: float
    :param interval_to: Maximum allowed value.
    :type interval_to: float
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value is not in interval.'

    def __init__(self, apply_to: Number, label: str, interval_from: float,
                 interval_to: float, error_message: Optional[str] = None,
                 stop_if_invalid: bool = False):
        """
                 Initialize an interval validation rule for numeric values.
                 
                 Parameters:
                     apply_to (Number): The numeric value to validate.
                     label (str): A descriptive label for the value being validated.
                     interval_from (float): The lower bound of the valid interval (inclusive).
                     interval_to (float): The upper bound of the valid interval (inclusive).
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.interval_from = interval_from
        self.interval_to = interval_to

    def apply(self) -> bool:
        """
        Return True if the target value is within the closed numeric interval [interval_from, interval_to].
        
        Returns:
            bool: True if the value is greater than or equal to interval_from and less than or equal to interval_to; False otherwise or if a data error occurs.
        """
        try:
            return self.interval_from <= self.apply_to <= self.interval_to
        except DATA_ERRORS:
            return False


class PatternRule(ValidationRule[str]):
    """
    Ensure that the target string respects the given pattern.

    :param apply_to: Value against which the rule is applied (can be any type).
    :type apply_to: object
    :param pattern: Regex used for pattern matching.
    :type pattern: str
    :param flags: Regex flags.
    :type flags: int
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Value does not match expected pattern.'

    def __init__(self, apply_to: str, label: str, pattern: str, flags: int = 0,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a string matches a specified regular expression pattern.
                 
                 Parameters:
                     apply_to (str): The string value to validate.
                     label (str): A descriptive label for the field being validated.
                     pattern (str): The regular expression pattern to match against.
                     flags (int, optional): Regular expression flags (e.g., re.IGNORECASE). Defaults to 0.
                     error_message (str, optional): Custom error message to use if validation fails.
                     stop_if_invalid (bool, optional): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.pattern = pattern
        self.flags = flags

    def apply(self) -> bool:
        """
        Return True if the target value is a string that matches the specified regular expression pattern.
        
        Returns:
            bool: True if the value is a string and matches the regex pattern; otherwise, False.
        """
        value = self.apply_to  # type: str
        return isinstance(value, str) and re.match(self.pattern, value, self.flags) is not None


class PastDateRule(ValidationRule):
    """
    Ensure that the target value is a past date.

    :param apply_to: Value against which the rule is applied.
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param reference_date: Date used for time checking (default to datetime.now()).
    :type reference_date: datetime
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Not a past date.'

    def __init__(self, apply_to: object, label: str, reference_date: Optional[datetime] = None,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a datetime value is before or after a reference date.
                 
                 Parameters:
                     apply_to (object): The value to validate, expected to be a datetime object.
                     label (str): A descriptive label for the field being validated.
                     reference_date (Optional[datetime]): The date to compare against. Defaults to the current datetime if not provided.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.reference_date = reference_date or datetime.now()

    def apply(self) -> bool:
        """
        Return True if the target value is a datetime object representing a date/time before the reference date.
        
        Returns:
            bool: True if the value is a datetime and is earlier than the reference date; False otherwise or if a data error occurs.
        """
        try:
            return isinstance(self.apply_to, datetime) and self.apply_to < self.reference_date
        except DATA_ERRORS:
            return False


class FutureDateRule(ValidationRule):
    """
    Ensure that the target value is a future date.

    :param apply_to: Value against which the rule is applied.
    :type apply_to: object
    :param label: Short string describing the field that will be validated (e.g. "phone number", "user name"...). \
    This string will be used as the key in the ValidationResult error dictionary.
    :type label: str
    :param reference_date: Date used for time checking (default to datetime.now()).
    :type reference_date: datetime
    :param error_message: Custom message that will be used instead of the "default_error_message".
    :type error_message: str
    :param stop_if_invalid: True to prevent Validator from processing the rest of the get_rules if the current one \
    is not respected, False (default) to collect all the possible errors.
    :type stop_if_invalid: bool
    """

    #: Default error message for the rule.
    default_error_message = 'Not a future date.'

    def __init__(self, apply_to: object, label: str, reference_date: Optional[datetime] = None,
                 error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
                 Initialize a validation rule that checks if a datetime value is before or after a reference date.
                 
                 Parameters:
                     apply_to (object): The value to validate, expected to be a datetime object.
                     label (str): A descriptive label for the field being validated.
                     reference_date (Optional[datetime]): The date to compare against. Defaults to the current datetime if not provided.
                     error_message (Optional[str]): Custom error message to use if validation fails.
                     stop_if_invalid (bool): Whether to halt further validation if this rule fails.
                 """
                 super().__init__(apply_to, label, error_message, stop_if_invalid)
        self.reference_date = reference_date or datetime.now()

    def apply(self) -> bool:
        """
        Return True if the target value is a datetime object representing a date/time after the reference date.
        
        Returns:
            bool: True if the value is a datetime and occurs after the reference date; False otherwise or if a data error occurs.
        """
        try:
            return isinstance(self.apply_to, datetime) and self.apply_to > self.reference_date
        except DATA_ERRORS:
            return False


class UniqueItemsRule(ValidationRule):
    """
    Ensure that the target list (or iterable) does not contain duplicated items.

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

    #: Default error message for the rule.
    default_error_message = 'List contains duplicated items.'

    def __init__(self, apply_to: object, label: str, error_message: Optional[str] = None, stop_if_invalid: bool = False):
        """
        Initialize a validation rule with the target value, label, optional custom error message, and a flag to stop further validation if the rule fails.
        """
        super().__init__(apply_to, label, error_message, stop_if_invalid)

    def _dictionary_items_are_unique(self):
        """
        Check whether all values in the target dictionary are unique by comparing each pair of consecutive values.
        
        Returns:
            bool: True if all consecutive values in the dictionary are unique; False if any adjacent duplicates are found.
        """
        data = self.apply_to  # type: dict
        values = list(data.values())
        if len(values) > 1:
            index = 1
            while index < len(values):
                if values[index - 1] == values[index]:
                    return False
                index += 1
        return True

    def _collection_items_are_unique(self):
        # noinspection PyTypeChecker
        """
        Check if all items in the target collection are unique.
        
        Returns:
            bool: True if the collection contains no duplicate items, False otherwise.
        """
        return len(set(self.apply_to)) == len(self.apply_to)

    def apply(self) -> bool:
        """
        Checks whether all items in the target collection are unique.
        
        For dictionaries, verifies that all values are unique. For sets, always returns True since sets are inherently unique. For other collections, checks that there are no duplicate items.
        
        Returns:
            bool: True if all items are unique; False if duplicates are found or if a data error occurs.
        """
        try:
            if isinstance(self.apply_to, dict):
                return self._dictionary_items_are_unique()
            if isinstance(self.apply_to, set):
                return True
            return self._collection_items_are_unique()
        except DATA_ERRORS:
            return False
