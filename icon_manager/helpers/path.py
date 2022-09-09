import os
from typing import Iterable, List, Optional, Sequence, Tuple

from icon_manager.interfaces.path import File, Folder


def get_parent_and_name(path: str) -> Tuple[str, str]:
    return os.path.split(path)


def get_name_and_extension(name: str) -> Tuple[str, Optional[str]]:
    splitted = name.split('.')
    if len(splitted) == 1:
        return splitted[0], None
    name = '.'.join(splitted[:-1])
    return name, splitted[-1]


def get_folder(entry: os.DirEntry) -> Folder:
    parent, name = get_parent_and_name(entry.path)
    parent = os.path.basename(parent)
    return Folder(parent_name=parent, path=entry.path, name=name,
                  excluded=False)


def create_file(entry: os.DirEntry) -> File:
    parent, name = get_parent_and_name(entry.path)
    name_wo_ext, ext = get_name_and_extension(entry.name)
    return File(parent_name=parent, path=entry.path, name=name,
                name_wo_ext=name_wo_ext, ext=ext, excluded=False)


def create_children_folder(parent: Folder) -> Folder:
    for entry in os.scandir(parent.path):
        if entry.is_dir():
            folder = get_folder(entry)
            parent.folders.append(folder)
        else:
            file = create_file(entry)
            parent.files.append(file)
    return parent


def create_folder(path: str, folders: List[Folder], files: List[File]) -> Folder:
    parent, name = get_parent_and_name(path)
    parent = os.path.basename(parent)
    return Folder(parent_name=parent, path=path, name=name,
                  folders=folders, files=files, excluded=False)


def crawle_folder(entry: os.DirEntry) -> Folder:
    files = []
    folders = []
    for elem in os.scandir(entry.path):
        if elem.is_dir():
            folders.append(crawle_folder(elem))
        else:
            files.append(create_file(elem))
    return create_folder(entry.path, folders, files)


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
