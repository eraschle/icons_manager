
import os
from typing import Iterable, List


def get_path_names(path: str) -> List[str]:
    splitted = path.split('/')
    if len(splitted) == 1:
        splitted = path.split('\\')
    return splitted


def is_file(path: str, name: str) -> bool:
    return os.path.isfile(os.path.join(path, name))


def get_files(path: str) -> List[str]:
    return [name for name in os.listdir(path) if is_file(path, name)]


def is_folder(path: str, name: str) -> bool:
    return os.path.isdir(os.path.join(path, name))


def get_folders(path: str) -> List[str]:
    return [name for name in os.listdir(path) if is_folder(path, name)]


def get_paths(path: str, names: Iterable[str]) -> List[str]:
    return [os.path.join(path, name) for name in names]
