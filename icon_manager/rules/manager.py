import logging
from typing import Iterable, Optional, Sequence

from icon_manager.interfaces.managers import (IAttributeRuleController,
                                              IConfigManager,
                                              IConfigRuleController)
from icon_manager.interfaces.path import Folder, JsonFile
from icon_manager.rules.base import ISingleRule, Operator, RuleAttribute

log = logging.getLogger(__name__)


class AttributeRuleHandler(IAttributeRuleController[Folder]):

    def __init__(self, attribute: RuleAttribute, operator: Operator,
                 rules: Sequence[ISingleRule]) -> None:
        """
                 Initialize an AttributeRuleHandler with a specific attribute, operator, and a sequence of single attribute rules.
                 
                 Parameters:
                     attribute (RuleAttribute): The attribute to which the rules apply.
                     operator (Operator): Determines whether all or any rules must be satisfied.
                     rules (Sequence[ISingleRule]): The collection of single attribute rules to manage.
                 """
                 self.attribute = attribute
        self.operator = operator
        self.rules = rules

    @property
    def name(self) -> str:
        return f'"{self.attribute.upper()}" Checker'

    def is_empty(self) -> bool:
        return all(rule.is_empty() for rule in self.rules)

    def clean_empty(self) -> None:
        rules = []
        for rule in self.rules:
            if rule.is_empty():
                continue
            rules.append(rule)
        self.rules = rules

    def is_allowed(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(rule.is_allowed(entry) for rule in self.rules)
        return any(rule.is_allowed(entry) for rule in self.rules)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for rule in self.rules:
            rule.set_before_or_after(before_or_after)
            rule.setup_filter_rule()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        """
        Return the string representation of the object for debugging purposes.
        """
        return self.__str__()


class ConfigRuleController(IConfigRuleController[Folder]):

    def __init__(self, checkers: Sequence[AttributeRuleHandler],
                 operator: Operator) -> None:
        """
                 Initialize the ConfigRuleController with a sequence of attribute rule handlers and a logical operator.
                 
                 Parameters:
                     checkers (Sequence[AttributeRuleHandler]): The attribute rule handlers to control.
                     operator (Operator): Determines how rule results are combined (ALL or ANY).
                 """
                 self.controllers = checkers
        self.operator = operator

    @property
    def name(self) -> str:
        """
        Return a string listing the attributes of all contained rule controllers.
        """
        attributes = ', '.join([checker.attribute.name
                               for checker in self.controllers])
        return f'Rule Checker [{attributes}]'

    def is_empty(self) -> bool:
        """
        Return True if all contained rule controllers are empty.
        """
        return all(checker.is_empty() for checker in self.controllers)

    def clean_empty(self) -> None:
        """
        Remove empty controllers from the internal list after cleaning each one.
        """
        controllers = []
        for checker in self.controllers:
            checker.clean_empty()
            if checker.is_empty():
                continue
            controllers.append(checker)
        self.controllers = controllers

    def is_allowed(self, entry: Folder) -> bool:
        """
        Determines if a folder entry is allowed by evaluating all contained rule controllers according to the configured operator.
        
        Returns:
            bool: True if the entry is allowed by all controllers when using the ALL operator, or by any controller otherwise.
        """
        if self.operator == Operator.ALL:
            return all(checker.is_allowed(entry) for checker in self.controllers)
        return any(rule.is_allowed(entry) for rule in self.controllers)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        """
        Configures all contained rule controllers with the provided context strings.
        
        Parameters:
            before_or_after (Iterable[str]): Context strings used to set up each controller's rules.
        """
        for checker in self.controllers:
            checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        """
        Return the string representation of the object, using its name property.
        """
        return self.name

    def __repr__(self) -> str:
        """
        Return the string representation of the object for debugging purposes.
        """
        return self.__str__()


class RuleManager(IConfigManager[Folder]):

    def __init__(self, config: JsonFile, checker: IConfigRuleController,
                 weight: int, copy_icon: Optional[bool]) -> None:
        """
                 Initialize a RuleManager with the given configuration file, rule controller, weight, and optional copy icon flag.
                 
                 Parameters:
                     config (JsonFile): The configuration file associated with this manager.
                     checker (IConfigRuleController): The rule controller used to evaluate entries.
                     weight (int): The priority or importance of this manager.
                     copy_icon (Optional[bool]): Whether to enable the copy icon feature.
                 """
                 self.config = config
        self.checker = checker
        self.weight = weight
        self.copy_icon = copy_icon

    @property
    def name(self) -> str:
        return self.config.name_wo_extension

    def is_empty(self) -> bool:
        return self.checker.is_empty()

    def clean_empty(self) -> None:
        self.checker.clean_empty()

    def is_allowed(self, entry: Folder) -> bool:
        return self.checker.is_allowed(entry)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        self.checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        name = self.config.name_wo_extension.upper()
        return f'"{name}" Manager'

    def __repr__(self) -> str:
        """
        Return the string representation of the object for debugging purposes.
        """
        return self.__str__()


class ExcludeManager(IConfigManager[Folder]):

    def __init__(self, checkers: Sequence[IConfigRuleController[Folder]]) -> None:
        """
        Initialize the ExcludeManager with a sequence of configuration rule controllers used for exclusion logic.
        """
        self.checkers = checkers

    def is_empty(self) -> bool:
        """
        Return True if all contained checkers are empty.
        
        Returns:
            bool: True if every checker in the collection is empty; otherwise, False.
        """
        return all(checker.is_empty() for checker in self.checkers)

    def clean_empty(self) -> None:
        """
        Remove empty checkers from the internal list after cleaning each one.
        
        This method calls `clean_empty()` on each contained checker, then retains only those that are not empty.
        """
        checkers = []
        for checker in self.checkers:
            checker.clean_empty()
            if checker.is_empty():
                continue
            checkers.append(checker)
        self.checkers = checkers

    def is_allowed(self, entry: Folder) -> bool:
        if self.is_empty():
            return True
        return any(manager.is_allowed(entry) for manager in self.checkers)

    def is_excluded(self, entry: Folder) -> bool:
        if self.is_empty():
            return False
        return self.is_allowed(entry)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for checker in self.checkers:
            checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        return f'Exclude Manager [{len(self.checkers)}]'

    def __repr__(self) -> str:
        return self.__str__()
