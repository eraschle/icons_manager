from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Protocol, runtime_checkable

from icon_manager.interfaces.path import Folder


class FolderAction(str, Enum):
    """What should happen to a crawled folder.

    The three outcomes the tool needs, which used to be spread over three
    differently-keyed predicates in the crawler's filters:

    - ``SKIP``: no icon, and nothing below it is looked at. For ``.git``,
      ``.venv``, ``node_modules``, ``__pycache__`` and the like.
    - ``LEAF``: the folder may get an icon, but nothing below it is looked
      at. For a code project, once ``project_depth`` is used up.
    - ``SEARCH``: the folder may get an icon and its children are looked at.
      The default for everything else.

    It lives here, with the other rule vocabulary, because an exclude rule
    carries the action it asks for and the crawler sits above the rules.
    """

    SKIP = "skip"
    LEAF = "leaf"
    SEARCH = "search"


class Operator(str, Enum):
    UNKNOWN = "unknown"
    ANY = "any"
    ALL = "all"


class RuleAttribute(str, Enum):
    UNKNOWN = "unknown"
    NAME = "name"
    PATH = "path"
    PARENT_NAME = "parent_name"
    PARENT_PATH = "parent_path"


class Rule(str, Enum):
    UNKNOWN = "unknown"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    STARTS_OR_ENDS_WITH = "start_or_ends_with"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    CHAINED = "chained"
    CONTAINS_FILE = "contains_file"
    NOT_CONTAINS_FILE = "not_contains_file"
    CONTAINS_FOLDER = "contains_folder"
    NOT_CONTAINS_FOLDER = "not_contains_folder"


class DepthAware(Protocol):
    """Reports how far below a folder it has to look.

    Narrower than :class:`FolderMatcher` on purpose: the crawler asks this
    of the exclude manager too, which answers ``action_for`` rather than
    ``is_allowed`` and is therefore not a matcher.
    """

    def required_depth(self) -> int:
        """How many levels below a folder this needs to see; 0 for none."""
        ...


@runtime_checkable
class FolderMatcher(Protocol):
    """Decides whether a folder matches a rule configuration.

    Every level of the rule tree satisfies this one protocol: a single rule
    on a folder attribute, a group of rules for the same attribute, the rule
    set of one icon configuration, and the exclude manager that combines
    several of those. Composing them is therefore a plain Composite -- a
    caller only ever needs ``is_allowed``.
    """

    @property
    def name(self) -> str:
        """Human readable name, used for logging and validation messages."""
        ...

    def is_allowed(self, entry: Folder) -> bool:
        """Whether ``entry`` satisfies this matcher."""
        ...

    def is_empty(self) -> bool:
        """Whether this matcher has no values to match against.

        An empty matcher can never produce a meaningful decision and is
        dropped by :meth:`clean_empty` of its parent.
        """
        ...

    def clean_empty(self) -> None:
        """Drop empty children. A leaf matcher has nothing to do here."""
        ...

    def setup_rules(self, before_or_after: Iterable[str]) -> None:
        """Prepare for matching, expanding rule values by ``before_or_after``.

        Must be called before the first :meth:`is_allowed`; the values are
        affixes (``_``, ``-``) that a folder name may carry around a rule
        value.
        """
        ...

    def required_depth(self) -> int:
        """How many levels below a folder this matcher has to see.

        0 for a matcher that only compares the folder's own name or path.
        ``contains_file`` and ``contains_folder`` need their ``level``, and a
        composite needs the deepest of its children. The crawler reads this
        to know how much it must materialise below a folder it is not going
        to descend into, so pruning the walk cannot change what a rule sees.
        """
        ...


class AFolderRule(ABC):
    """Base for a single rule on one folder attribute."""

    def __init__(self, attribute: RuleAttribute, operator: Operator) -> None:
        super().__init__()
        self.attribute = attribute
        self.operator = operator

    @property
    def name(self) -> str:
        return f"Rule {self.attribute.name} [{self.operator.name}]"

    def clean_empty(self) -> None:  # noqa: B027 - a leaf rule has no children
        """A single rule has no children to clean."""

    def required_depth(self) -> int:
        """A rule on the folder's own attributes needs nothing below it."""
        return 0

    @abstractmethod
    def is_empty(self) -> bool: ...

    @abstractmethod
    def is_allowed(self, entry: Folder) -> bool: ...

    @abstractmethod
    def setup_rules(self, before_or_after: Iterable[str]) -> None: ...

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} {self.attribute} [{self.operator.name}]"


class AAttributeRule(AFolderRule):
    """A single rule that compares one folder attribute against its values."""

    def is_allowed(self, entry: Folder) -> bool:
        value = getattr(entry, self.attribute.value, None)
        if value is None or self.operator == Operator.UNKNOWN:
            return False
        value = self.prepare_element_value(value)
        if self.operator == Operator.ALL:
            return self.are_all_allowed(entry, value)
        return self.are_any_allowed(entry, value)

    @abstractmethod
    def prepare_element_value(self, value: str) -> str: ...

    @abstractmethod
    def are_any_allowed(self, entry: Folder, value: str) -> bool: ...

    @abstractmethod
    def are_all_allowed(self, entry: Folder, value: str) -> bool: ...
