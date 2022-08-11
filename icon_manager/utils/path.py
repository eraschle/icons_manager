
from typing import List


def get_path_names(path: str) -> List[str]:
    splitted = path.split('/')
    if len(splitted) == 1:
        splitted = path.split('\\')
    return splitted
