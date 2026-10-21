from icon_manager.rules.base import FolderMatcher, Rule
from icon_manager.rules.rules import (
    ChainedRule,
    ContainsFileRule,
    ContainsFolderRule,
    ContainsRule,
    EndsWithRule,
    EqualsRule,
    NotContainsFileRule,
    NotContainsFolderRule,
    NotContainsRule,
    NotEqualsRule,
    StartsOrEndsWithRule,
    StartsWithRule,
)

RULES: dict[Rule, type[FolderMatcher]] = {
    Rule.EQUALS: EqualsRule,
    Rule.NOT_EQUALS: NotEqualsRule,
    Rule.STARTS_WITH: StartsWithRule,
    Rule.ENDS_WITH: EndsWithRule,
    Rule.STARTS_OR_ENDS_WITH: StartsOrEndsWithRule,
    Rule.CONTAINS: ContainsRule,
    Rule.NOT_CONTAINS: NotContainsRule,
    Rule.CHAINED: ChainedRule,
    Rule.CONTAINS_FILE: ContainsFileRule,
    Rule.NOT_CONTAINS_FILE: NotContainsFileRule,
    Rule.CONTAINS_FOLDER: ContainsFolderRule,
    Rule.NOT_CONTAINS_FOLDER: NotContainsFolderRule,
}


def rule_mapping() -> dict[Rule, type[FolderMatcher]]:
    """The rule name used in a config file to the class implementing it.

    Every member of :class:`Rule` except ``UNKNOWN`` has an entry, which is
    asserted by ``test_rules.py``; a missing one used to only log a warning
    and then silently ignore that rule in every config file.
    """
    return dict(RULES)
