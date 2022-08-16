PREFIX_LENGTH = 15

HUNDRED = 3
THOUSAND = 4
FILL_SPACE = ' '
FILL_HYPHEN = '-'


def fixed_length(value: str, width: int, fill: str = FILL_SPACE, align: str = '>') -> str:
    return f"{value:{fill}{align}{width}}"
