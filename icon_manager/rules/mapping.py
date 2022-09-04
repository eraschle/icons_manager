from typing import Dict, Type

from icon_manager.rules.base import IconRule
from icon_manager.rules.rules import (ChainedRule, ContainsFileRule,
                                      ContainsRule, EndswithRule, EqualsRule,
                                      NotContainsRule, NotEqualsRule,
                                      StartsOrEndswithRule, StartswithRule)

RULE_MAPPINGS: Dict[str, Type[IconRule]] = {
    'equals': EqualsRule,
    "not_equals": NotEqualsRule,
    "starts_with": StartswithRule,
    "ends_with": EndswithRule,
    "start_or_ends_with": StartsOrEndswithRule,
    'contains': ContainsRule,
    'not_contains': NotContainsRule,
    'chained': ChainedRule,
    'contains_files': ContainsFileRule
}
