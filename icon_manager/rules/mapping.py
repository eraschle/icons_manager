import logging
from typing import Dict, Type

from icon_manager.rules.base import ISingleRule, Rule
from icon_manager.rules.rules import *

log = logging.getLogger(__name__)


def is_rule(rule_class) -> bool:
    return rule_class is not None and rule_class.__name__ != 'NoneType'


def _rule_class_name(rule: Rule) -> str:
    splitted_name = rule.name.split('_')
    splitted_name.append('Rule')
    return ''.join([name.capitalize() for name in splitted_name])


def rule_mapping() -> Dict[Rule, Type[ISingleRule]]:
    rules = {}
    for rule in Rule:
        if rule == Rule.UNKNOWN:
            continue
        rule_class = globals().get(_rule_class_name(rule))
        if rule_class is None or not is_rule(rule_class):
            log.warning('No rule for >> %s <<' % rule)
            continue
        rules[rule] = rule_class
    return rules
