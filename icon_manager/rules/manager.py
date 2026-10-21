import logging
from collections.abc import Iterable, Sequence

from icon_manager.interfaces.path import Folder, JsonFile
from icon_manager.rules.base import FolderAction, FolderMatcher, Operator, RuleAttribute

log = logging.getLogger(__name__)


class AttributeRuleHandler:
    def __init__(self, attribute: RuleAttribute, operator: Operator, rules: Sequence[FolderMatcher]) -> None:
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
            rule.setup_rules(before_or_after)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ConfigRuleController:
    """The rule set of one icon config: an attribute handler per section.

    Typed to AttributeRuleHandler rather than FolderMatcher because it reads
    each child's ``attribute`` to build its own name.
    """

    def __init__(self, controllers: Sequence[AttributeRuleHandler], operator: Operator) -> None:
        self.controllers = controllers
        self.operator = operator

    @property
    def name(self) -> str:
        attributes = ", ".join([checker.attribute.name for checker in self.controllers])
        return f"Rule Checker [{attributes}]"

    def is_empty(self) -> bool:
        return all(checker.is_empty() for checker in self.controllers)

    def clean_empty(self) -> None:
        controllers = []
        for checker in self.controllers:
            checker.clean_empty()
            if checker.is_empty():
                continue
            controllers.append(checker)
        self.controllers = controllers

    def is_allowed(self, entry: Folder) -> bool:
        if self.operator == Operator.ALL:
            return all(checker.is_allowed(entry) for checker in self.controllers)
        return any(checker.is_allowed(entry) for checker in self.controllers)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for checker in self.controllers:
            checker.setup_rules(before_or_after)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class RuleManager:
    def __init__(self, config: JsonFile, checker: FolderMatcher, order: int, copy_icon: bool | None) -> None:
        self.config = config
        self.checker = checker
        self.order = order
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
        return self.__str__()


class ExcludeRule:
    """One section of ``excluded_rules.config`` and the action it asks for.

    ``action`` is the section's ``"action"`` key: ``skip`` (the default, no
    icon and nothing below it is looked at) or ``leaf`` (the folder may get
    an icon, but nothing below it is looked at).
    """

    def __init__(self, matcher: FolderMatcher, action: FolderAction = FolderAction.SKIP) -> None:
        self.matcher = matcher
        self.action = action

    @property
    def name(self) -> str:
        return f"{self.matcher.name} [{self.action.value}]"

    def is_empty(self) -> bool:
        return self.matcher.is_empty()

    def clean_empty(self) -> None:
        self.matcher.clean_empty()

    def is_allowed(self, entry: Folder) -> bool:
        return self.matcher.is_allowed(entry)

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        self.matcher.setup_rules(before_or_after)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ExcludeManager:
    """The rule sections of ``excluded_rules.config``, in file order."""

    def __init__(self, rules: Sequence[ExcludeRule]) -> None:
        self.rules = rules

    @property
    def name(self) -> str:
        return f"Exclude Manager [{len(self.rules)}]"

    def is_empty(self) -> bool:
        return all(rule.is_empty() for rule in self.rules)

    def clean_empty(self) -> None:
        kept = []
        for rule in self.rules:
            rule.clean_empty()
            if rule.is_empty():
                continue
            kept.append(rule)
        self.rules = kept

    def action_for(self, entry: Folder) -> FolderAction | None:
        """The action of the first section matching ``entry``, else None.

        First match wins, in the order the sections appear in the file, so
        two sections disagreeing about the same folder is decided by where
        they are written rather than silently.
        """
        for rule in self.rules:
            if rule.is_allowed(entry):
                return rule.action
        return None

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        for rule in self.rules:
            rule.setup_rules(before_or_after)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()
