from typing import Any, Sequence


PREFIX_LENGTH = 15

HUNDRED = 3
THOUSAND = 4
FILL_SPACE = ' '
FILL_HYPHEN = '-'


def fixed_length(value: str, width: int, fill: str = FILL_SPACE, align: str = '>') -> str:
    return f"{value:{fill}{align}{width}}"


def prefix_value(value: str, align: str = '>') -> str:
    return fixed_length(value, PREFIX_LENGTH, align=align)


def list_value(values: Sequence[Any], align: str = '<') -> str:
    return fixed_length(str(len(values)), THOUSAND, align=align)
