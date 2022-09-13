import os
from typing import Iterable, List, Optional, Sequence, Tuple

from icon_manager.interfaces.path import File, Folder


def crawle_folder(entry: os.DirEntry, parent: Optional[Folder]) -> Folder:
    current = Folder.from_path(entry.path, parent)
    for elem in os.scandir(entry.path):
        if elem.is_dir():
            current.folders.append(crawle_folder(elem, current))
        else:
            current.files.append(File.from_path(elem.path, current))
    return current


def is_file(path: str, name: str, extension: Optional[str] = None) -> bool:
    if not os.path.isfile(os.path.join(path, name)):
        return False
    if extension is None:
        return True
    if not extension.startswith('.'):
        extension = f'.{extension}'
    return name.endswith(extension)


def is_file_extensions(file: File, extensions: Sequence[str]) -> bool:
    return file.ext is not None and file.ext in extensions


def get_files(path: str, extension: Optional[str] = None) -> List[str]:
    return [name for name in os.listdir(path) if is_file(path, name, extension)]


def get_path(path: str, name: str) -> str:
    return os.path.join(path, name)


def get_paths(path: str, names: Iterable[str]) -> List[str]:
    return [get_path(path, name) for name in names]


def count_of(folder: Folder) -> Tuple[int, int]:
    return len(folder.folders), len(folder.files)


def count_of_recursive(entry: Folder) -> Iterable[Tuple[int, int]]:
    counts = [count_of(entry)]
    for folder in entry.folders:
        counts.extend(count_of_recursive(folder))
    return counts


def total_count(entries: Iterable[Folder]) -> Tuple[int, int]:
    counts: List[Tuple[int, int]] = []
    for entry in entries:
        counts.extend(count_of_recursive(entry))
    return (sum([count[0] for count in counts]),
            sum([count[1] for count in counts]))
