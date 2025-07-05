from collections.abc import Sequence
from typing import Any

PREFIX_LENGTH = 15

HUNDRED = 3
THOUSAND = 4
FILL_SPACE = " "
FILL_HYPHEN = "-"

ALIGN_LEFT = "<"
ALIGN_RIGHT = ">"
ALIGN_CENTRE = "^"


def fixed_length(value: str, width: int, fill: str = FILL_SPACE, align: str = ALIGN_LEFT) -> str:
    return f"{value:{fill}{align}{width}}"


def prefix_value(value: str, width: int = PREFIX_LENGTH, align: str = ALIGN_LEFT) -> str:
    return fixed_length(value, width=width, align=align)


def list_value(values: Sequence[Any], width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    return fixed_length(str(len(values)), width=width, align=align)
