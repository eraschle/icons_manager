import logging
import os
from collections import namedtuple
from typing import Iterable, List, Optional, Sequence, Tuple, Union

log = logging.getLogger(__name__)


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


def get_path(path: str, name: str) -> str:
    return os.path.join(path, name)


def get_paths(path: str, names: Iterable[str]) -> List[str]:
    return [get_path(path, name) for name in names]


File = namedtuple('File', ['path', 'name', 'extension'])


def is_file_extensions(file: File, extensions: Sequence[str]) -> bool:
    return file.extension is not None and file.extension in extensions


Folder = namedtuple('Folder', ['path', 'name', 'folders', 'files'])
Path = Union[Folder, File]


def create_file(path: str, name: str) -> File:
    splitted = name.split('.')
    extension: Optional[str] = splitted[-1]
    if len(splitted) <= 1:
        extension = None
    return File(path=path, name=name, extension=extension)


def crawle_folder(entry: os.DirEntry) -> Folder:
    files = []
    folders = []
    for elem in os.scandir(entry.path):
        if elem.is_dir():
            folders.append(crawle_folder(elem))
        else:
            files.append(create_file(elem.path, elem.name))
    return Folder(path=entry.path, name=entry.name, files=files, folders=folders)


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
