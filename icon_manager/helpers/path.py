import os
from typing import List, Optional


def is_file(path: str, name: str, extension: Optional[str] = None) -> bool:
    if not os.path.isfile(os.path.join(path, name)):
        return False
    if extension is None:
        return True
    if not extension.startswith('.'):
        extension = f'.{extension}'
    return name.endswith(extension)


def get_files(path: str, extension: Optional[str] = None) -> List[str]:
    return [name for name in os.listdir(path) if is_file(path, name, extension)]
