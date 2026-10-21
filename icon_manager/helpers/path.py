import os
from collections.abc import Iterable

from icon_manager.interfaces.path import Folder


def is_file(path: str, name: str, extension: str | None = None) -> bool:
    if not os.path.isfile(os.path.join(path, name)):
        return False
    if extension is None:
        return True
    if not extension.startswith("."):
        extension = f".{extension}"
    return name.endswith(extension)


def get_files(path: str, extension: str | None = None) -> list[str]:
    return [name for name in os.listdir(path) if is_file(path, name, extension)]


def get_path(path: str, name: str) -> str:
    return os.path.join(path, name)


def get_paths(path: str, names: Iterable[str]) -> list[str]:
    return [get_path(path, name) for name in names]


def count_of(folder: Folder) -> tuple[int, int]:
    return len(folder.folders), len(folder.files)


def count_of_recursive(entry: Folder) -> Iterable[tuple[int, int]]:
    counts = [count_of(entry)]
    for folder in entry.folders:
        counts.extend(count_of_recursive(folder))
    return counts


def total_count(entries: Iterable[Folder]) -> tuple[int, int]:
    counts: list[tuple[int, int]] = []
    for entry in entries:
        counts.extend(count_of_recursive(entry))
    return (sum([count[0] for count in counts]), sum([count[1] for count in counts]))
