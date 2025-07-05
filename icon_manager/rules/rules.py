import logging
from abc import abstractmethod
from typing import Any, Collection, Iterable, Sequence, Set

from icon_manager.interfaces.path import Folder
from icon_manager.rules.base import (AFilterRule, ASingleRule, ISingleRule,
                                     Operator, RuleAttribute)
from icon_manager.rules.generate import (AfterGenerator, BeforeGenerator,
                                         BeforeOrAfterGenerator, CaseConverter,
                                         Generator, GeneratorManager)

log = logging.getLogger(__name__)


# region FOLDER RULES


class IRuleValuesFilter(ISingleRule):
    operator: Operator
    attribute: RuleAttribute
    rule_values: Collection[str]
    is_case_sensitive: bool

    @property
    def name(self) -> str:
        """
        Returns the name of the rule.
        
        This property should be implemented by subclasses to provide a unique identifier or descriptive name for the rule instance.
        """
        ...

    def is_allowed(self, entry: Folder) -> bool:
        """
        Determines whether the given folder entry satisfies the rule's filtering criteria.
        
        Parameters:
        	entry (Folder): The folder entry to evaluate.
        
        Returns:
        	bool: True if the entry is allowed by the rule, otherwise False.
        """
        ...

    def is_empty(self) -> bool:
        """
        Return True if the rule has no values set and will not filter any entries.
        """
        ...

    def set_before_or_after(self, values: Iterable[str]) -> None:
        """
        Configures the rule to generate additional matching values based on "before" or "after" patterns using the provided values.
        """
        ...

    def setup_filter_rule(self) -> None:
        """
        Prepares the filter rule by processing and generating any additional rule values needed for filtering.
        
        This typically involves converting rule values and applying any configured generators or transformations.
        """
        ...

    def prepare_rule_values(self, values: Collection[str]) -> Collection[str]:
        """
        Converts and prepares a collection of rule values for use in filtering operations.
        
        Parameters:
            values (Collection[str]): The input rule values to be processed.
        
        Returns:
            Collection[str]: The processed and converted rule values ready for rule evaluation.
        """
        ...

    def prepare_element_value(self, value: str) -> str:
        """
        Convert and return the given value using the rule's configured value converters.
        
        Parameters:
            value (str): The value to be converted.
        
        Returns:
            str: The converted value.
        """
        ...


class FolderRule(ASingleRule):

    def __init__(self, attribute: RuleAttribute, operator: Operator,
                 rule_values: Collection[str], case_sensitive: bool,
                 before_or_after: bool, before_or_after_values: Collection[str]) -> None:
        """
                 Initializes a FolderRule with specified attribute, operator, rule values, case sensitivity, and optional before/after value generation.
                 
                 Parameters:
                     attribute (RuleAttribute): The folder attribute to which the rule applies.
                     operator (Operator): The comparison operator for the rule.
                     rule_values (Collection[str]): The set of values used for rule matching.
                     case_sensitive (bool): Whether string comparisons are case sensitive.
                     before_or_after (bool): Whether to generate additional values based on before/after patterns.
                     before_or_after_values (Collection[str]): Values used for before/after pattern generation.
                 """
                 super().__init__(attribute, operator)
        self.original_values = list(rule_values)
        self.generated: Collection[str] = []
        self.rule_values = rule_values
        self.generator = GeneratorManager()
        self.is_case_sensitive = case_sensitive
        self.add_before_or_after_values = before_or_after
        self.generator.set_values(before_or_after_values)
        self.generator.converters = [CaseConverter(case_sensitive)]

    def is_empty(self) -> bool:
        return len(self.rule_values) == 0

    def get_generators(self) -> Sequence[Generator]:
        return [BeforeGenerator(), AfterGenerator(), BeforeOrAfterGenerator()]

    def before_and_after_generators(self) -> Sequence[Generator]:
        return [BeforeGenerator(), AfterGenerator()]

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        if not self.add_before_or_after_values:
            return
        self.generator.generators = self.get_generators()
        self.generator.set_generator_values(before_or_after)

    def _before_or_after(self, values: Collection[str]) -> Collection[str]:
        if not self.add_before_or_after_values:
            return []
        include_value = False
        return self.generator.generates_unique(values, include_value)

    def setup_filter_rule(self) -> None:
        self.rule_values = self.prepare_rule_values(self.original_values)
        self.generated = self._before_or_after(self.rule_values)

    def prepare_rule_values(self, values: Collection[str]) -> Collection[str]:
        return self.generator.converts(values)

    def prepare_element_value(self, value: str) -> str:
        return self.generator.convert(value)

    def are_any_allowed(self, entry: Folder, value: Any) -> bool:
        if self._are_any_allowed(entry, value, self.rule_values):
            return True
        if len(self.generated) == 0:
            return False
        return self._are_any_allowed(entry, value, self.generated)

    def _are_any_allowed(self, entry: Folder, value: Any, rule_values: Iterable[str]) -> bool:
        return any(self.is_value_allowed(entry, value, rule_value) for rule_value in rule_values)

    def are_all_allowed(self, entry: Folder, value: Any) -> bool:
        if self._are_all_allowed(entry, value, self.rule_values):
            return True
        if len(self.generated) == 0:
            return False
        return self._are_all_allowed(entry, value, self.generated)

    def _are_all_allowed(self, entry: Folder, value: Any, rule_values: Iterable[str]) -> bool:
        return all(self.is_value_allowed(entry, value, rule_value) for rule_value in rule_values)

    @abstractmethod
    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        pass

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute} {self.rule_values}'

    def __repr__(self) -> str:
        return self.__str__()


class EqualsRule(FolderRule):

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given value is exactly equal to the rule value.
        
        Parameters:
            value (str): The value to compare.
            rule_value (str): The rule value to compare against.
        
        Returns:
            bool: True if value equals rule_value, otherwise False.
        """
        return rule_value == value


class NotEqualsRule(EqualsRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given value does not satisfy the parent rule's condition for the specified entry and rule value.
        
        This method inverts the result of the parent class's `is_value_allowed` method.
        """
        return not super().is_value_allowed(entry, value, rule_value)


class ContainsRule(FolderRule):

    def get_generators(self) -> Sequence[Generator]:
        """
        Return the sequence of generators used for producing additional rule values based on "before" and "after" patterns.
        """
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        """
        Checks if the rule value is a substring of the provided value.
        
        Returns:
            bool: True if `rule_value` is found within `value`, otherwise False.
        """
        return rule_value in value


class NotContainsRule(ContainsRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        return not super().is_value_allowed(entry, value, rule_value)


class StartsWithRule(FolderRule):

    def get_generators(self) -> Sequence[Generator]:
        """
        Return the sequence of generators used for producing additional rule values based on "before" and "after" patterns.
        """
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given string value starts with the specified rule value.
        
        Parameters:
            value (str): The string to check.
            rule_value (str): The prefix to match.
        
        Returns:
            bool: True if value starts with rule_value, otherwise False.
        """
        return value.startswith(rule_value)


class EndsWithRule(FolderRule):

    def get_generators(self) -> Sequence[Generator]:
        """
        Return the sequence of generators used for producing additional rule values based on "before" and "after" patterns.
        """
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given string value ends with the specified rule value.
        
        Parameters:
            value (str): The string to check.
            rule_value (str): The suffix to match.
        
        Returns:
            bool: True if value ends with rule_value, otherwise False.
        """
        return value.endswith(rule_value)


class StartsOrEndsWithRule(FolderRule):

    def get_generators(self) -> Sequence[Generator]:
        """
        Return the sequence of generators used for producing additional rule values based on "before" and "after" patterns.
        """
        return self.before_and_after_generators()

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given value starts or ends with the specified rule value.
        
        Parameters:
            value (str): The string to check.
            rule_value (str): The prefix or suffix to match.
        
        Returns:
            bool: True if value starts or ends with rule_value, otherwise False.
        """
        return value.startswith(rule_value) or value.endswith(rule_value)


class IPathOperationRule(IRuleValuesFilter):
    operator: Operator
    attribute: RuleAttribute
    rule_values: Collection[str]
    is_case_sensitive: bool
    max_level: int

    @property
    def name(self) -> str:
        """
        Returns the name of the rule.
        
        This property should be implemented by subclasses to provide a unique identifier or descriptive name for the rule instance.
        """
        ...

    def is_allowed(self, entry: Folder) -> bool:
        """
        Determines whether the given folder entry satisfies the rule's filtering criteria.
        
        Parameters:
        	entry (Folder): The folder entry to evaluate.
        
        Returns:
        	bool: True if the entry is allowed by the rule, otherwise False.
        """
        ...

    def is_empty(self) -> bool:
        """
        Return True if the rule has no values set and will not filter any entries.
        """
        ...

    def set_before_or_after(self, values: Iterable[str]) -> None:
        """
        Configures the rule to generate additional matching values based on "before" or "after" patterns using the provided values.
        """
        ...

    def setup_filter_rule(self) -> None:
        """
        Prepares the filter rule by processing and generating any additional rule values needed for filtering.
        
        This typically involves converting rule values and applying any configured generators or transformations.
        """
        ...

    def prepare_rule_values(self, values: Collection[str]) -> Collection[str]:
        """
        Converts and prepares a collection of rule values for use in filtering operations.
        
        Parameters:
            values (Collection[str]): The input rule values to be processed.
        
        Returns:
            Collection[str]: The processed and converted rule values ready for rule evaluation.
        """
        ...

    def prepare_element_value(self, value: str) -> str:
        """
        Convert and return the given value using the rule's configured value converters.
        
        Parameters:
            value (str): The value to be converted.
        
        Returns:
            str: The converted value.
        """
        ...


class ContainsFileRule(FolderRule, IPathOperationRule):

    def __init__(self, attribute: RuleAttribute, operator: Operator, values: Collection[str],
                 case_sensitive: bool, before_or_after: bool,
                 before_or_after_values: Collection[str], level: int) -> None:
        """
                 Initialize a ContainsFileRule for filtering folders by file extension presence up to a specified directory depth.
                 
                 Parameters:
                     attribute (RuleAttribute): The folder attribute to apply the rule to.
                     operator (Operator): The comparison operator for the rule.
                     values (Collection[str]): File extension values to match.
                     case_sensitive (bool): Whether matching is case sensitive.
                     before_or_after (bool): Whether to generate additional rule values based on before/after patterns.
                     before_or_after_values (Collection[str]): Values used for before/after pattern generation.
                     level (int): Maximum directory depth to search for matching file extensions.
                 """
                 super().__init__(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values)
        self.max_level = level
        self.replace_values = ['*', '.']

    def get_generators(self) -> Sequence[Generator]:
        return []

    def get_rule_value(self, value: str) -> str:
        for replace in self.replace_values:
            if not value.startswith(replace):
                continue
            value = value.lstrip(replace)
        return value

    def prepare_rule_values(self, values: Collection[str]) -> Collection[str]:
        values = [self.get_rule_value(value) for value in values]
        return super().prepare_rule_values(values)

    def get_extensions_of(self, folder: Folder) -> Set[str]:
        extensions = [file.ext for file in folder.files]
        return set([ext for ext in extensions if ext is not None])

    def get_extensions(self, entry: Folder, level: int) -> Iterable[str]:
        """
        Recursively collects all file extensions within a folder and its subfolders up to the specified maximum depth.
        
        Parameters:
            entry (Folder): The folder to search for file extensions.
            level (int): The current recursion depth.
        
        Returns:
            Iterable[str]: A set of unique file extensions found within the folder hierarchy up to max_level.
        """
        extensions = self.get_extensions_of(entry)
        level += 1
        if level >= self.max_level:
            return extensions
        for folder in entry.folders:
            extensions.update(self.get_extensions(folder, level))
        return extensions

    def is_value_allowed(self, entry: Folder, _: str, rule_value: str) -> bool:
        """
        Checks if any file extension in the folder (or its parent, depending on the attribute) ends with the specified rule value.
        
        Returns:
            bool: True if at least one file extension matches the rule value; otherwise, False.
        """
        folder = entry
        if self.attribute == RuleAttribute.PARENT_PATH and entry.parent is not None:
            folder = entry.parent
        extensions = self.get_extensions(folder, level=0)
        return any(ext.endswith(rule_value) for ext in extensions)


class NotContainsFileRule(ContainsFileRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given value does not satisfy the parent rule's condition for the specified entry and rule value.
        
        This method inverts the result of the parent class's `is_value_allowed` method.
        """
        return not super().is_value_allowed(entry, value, rule_value)


class ContainsFolderRule(ContainsFileRule):
    def __init__(self, attribute: RuleAttribute, operator: Operator, values: Collection[str],
                 case_sensitive: bool, before_or_after: bool,
                 before_or_after_values: Collection[str], level: int) -> None:
        super().__init__(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values, level)
        self.replace_values = []

    def get_generators(self) -> Sequence[Generator]:
        return []

    def get_folder_names(self, folder: Folder) -> Set[str]:
        names = [folder.name for folder in folder.folders]
        return set(names)

    def get_folders(self, entry: Folder, level: int) -> Iterable[str]:
        """
        Recursively collects the names of all folders within a folder hierarchy up to the specified maximum level.
        
        Parameters:
            entry (Folder): The root folder from which to start collecting folder names.
            level (int): The current recursion depth.
        
        Returns:
            Iterable[str]: A set of folder names found within the hierarchy up to the maximum level.
        """
        folders = self.get_folder_names(entry)
        level += 1
        if level >= self.max_level:
            return folders
        for folder in entry.folders:
            folders.update(self.get_folders(folder, level))
        return folders

    def is_value_allowed(self, entry: Folder, _: str, rule_value: str) -> bool:
        """
        Check if any folder name within the specified folder (or its parent, depending on the attribute) matches the given rule value.
        
        Returns:
            bool: True if at least one folder name equals the rule value; otherwise, False.
        """
        folder = entry
        if self.attribute == RuleAttribute.PARENT_PATH and entry.parent is not None:
            folder = entry.parent
        folder_names = self.get_folders(folder, level=0)
        return any(name == rule_value for name in folder_names)


class NotContainsFolderRule(ContainsFolderRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        """
        Return True if the given value does not satisfy the parent rule's condition for the specified entry and rule value.
        
        This method inverts the result of the parent class's `is_value_allowed` method.
        """
        return not super().is_value_allowed(entry, value, rule_value)


# endregion


class ChainedRule(AFilterRule, ISingleRule):

    def __init__(self, attribute: RuleAttribute, operator: Operator,
                 rules: Sequence[ISingleRule]) -> None:
        super().__init__(attribute, operator)
        self.rules = rules

    def is_empty(self) -> bool:
        if len(self.rules) == 0:
            return True
        return all(rule.is_empty() for rule in self.rules)

    def is_allowed(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(rule.is_allowed(entry) for rule in self.rules)
        return any(rule.is_allowed(entry) for rule in self.rules)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        for rule in self.rules:
            rule.set_before_or_after(before_or_after)

    def setup_filter_rule(self) -> None:
        for rule in self.rules:
            rule.setup_filter_rule()
