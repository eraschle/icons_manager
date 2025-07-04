import logging
import os

from icon_manager.helpers.string import (
    ALIGN_CENTRE,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    fixed_length,
)

log = logging.getLogger(__name__)


# region MESSAGE GENERATION


def _short_value(value: str, width=5, align=ALIGN_RIGHT):
    return f"{fixed_length(value, width=width, align=align)}"


def _long_value(value: str, width=10, align=ALIGN_RIGHT):
    return f"{fixed_length(value, width=width, align=align)}"


def _prefix_value(prefix):
    return f"{fixed_length(prefix, width=15, align=ALIGN_LEFT)}"


def _rule_name(rule, width=15):
    return _long_value(rule.name, width=width, align=ALIGN_LEFT)


def _rule_logic(rule, width=5):
    return _short_value(rule.operator.name.upper(), width=width, align=ALIGN_CENTRE)


def _rule_values(rule):
    return ", ".join(rule.original_values)


def _attr_name(rule):
    return _short_value(rule.attribute, width=5, align=ALIGN_LEFT)


def _rule_log(rule):
    logic = _short_value(rule.operator, width=4, align=ALIGN_RIGHT)
    attr = _attr_name(rule)
    name = _rule_name(rule)
    return f'{name.title()} with {logic.upper()}-logic on "{attr.upper()}"'


def _value_with_width(value: str, width):
    if value is None or len(value) < width:
        return value
    epsilon = "..."
    max_idx = width - len(epsilon)
    return value[:max_idx] + epsilon


def bool_as_str(value: bool):
    return "YES" if value else "NO"


def _value_log(rule, *args):
    width = 50
    value = _value_with_width(args[1], width)
    attr_value = _long_value(value, width=width, align=ALIGN_RIGHT)
    value = _value_with_width(args[2], width)
    rule_value = _long_value(value, width=width, align=ALIGN_LEFT)
    bool_val = bool_as_str(rule.is_case_sensitive)
    is_case = _short_value(bool_val, width=6, align=ALIGN_LEFT)
    bool_val = bool_as_str(rule.add_before_or_after_values)
    surround = _short_value(bool_val, width=6, align=ALIGN_LEFT)
    return f'Attr "{attr_value}" == "{rule_value}" Rule [case: {is_case} for//after: {surround}]'


def _elem_message(elem):
    elem_value = _elem_name(elem)
    parent, _ = os.path.split(_elem_path(elem))
    log.debug(f"{elem_value} [{parent}]")


LOG_MATCH_VALUES: bool = False


def matched_value():
    def actual_decorator(func):
        def matching(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not LOG_MATCH_VALUES:
                return result
            if result is True:
                log.info(_rule_log(self))
                log.info(_elem_message(args[0]))
                log.info(_value_log(self, *args))
            return result

        return matching

    return actual_decorator


# endregion


# region MATCHED_RULE


def _match_rule_names(rule):
    prefix = _prefix_value("RULE-INFO")
    name_val = _rule_name(rule, width=12)
    name_val = _rule_name(rule, width=12)
    attr_val = _attr_name(rule)
    return f"{prefix} {name_val} {attr_val}"


def _match_rule_values(rule):
    prefix = _prefix_value("WERTE")
    logic_val = _rule_logic(rule)
    values = _rule_values(rule)
    return f'{prefix} {logic_val} "{values}"'


def _elem_name(elem):
    name = getattr(elem, "name", "*** NO NAME ***")
    return _long_value(name, width=20, align=ALIGN_LEFT)


def _elem_path(elem, width=30, align=ALIGN_LEFT):
    path = getattr(elem, "path", "*** NO PATH ***")
    parent, _ = os.path.split(path)
    parent = _long_value(parent, width=width, align=align)
    return _value_with_width(parent, width=width)


def _elem_value(elem, rule, width=25, align=ALIGN_LEFT):
    value = getattr(elem, rule.attribute)
    value = _long_value(value, width=width, align=align)
    return _value_with_width(value, width=width)


def _elem_attr_name(rule, width=15, align=ALIGN_LEFT):
    value = _long_value(rule.attribute, width=width, align=align)
    return _value_with_width(value, width=width)


def _match_elem_log(elem, rule):
    prefix = _prefix_value("ELEMENT-INFO:")
    name = _elem_name(elem)
    attr = _elem_attr_name(rule)
    value = _elem_value(elem, rule)
    # path = _elem_path(elem)
    return f'{prefix}: {name} [{attr}] "{value}"'
    # return f'{prefix}: {name} [{attr}] "{value}" [{path}]'


LOG_MATCH_RULES: bool = False


def matched_rule():
    def actual_decorator(func):
        def matching(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not LOG_MATCH_RULES:
                return result
            if result is True:
                log.info(_match_rule_names(self))
                # log.info(_match_rule_values(self))
                log.info(_match_elem_log(args[0], self))
            return result

        return matching

    return actual_decorator


# endregion
