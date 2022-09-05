from typing import Iterable, List, Optional, Sequence
from unittest import result

from icon_manager.helpers.path import File, Folder
from icon_manager.crawler.options import FilterOptions

EXCLUDED_FOLDERS: Iterable[str] = []


def _is_excluded(folder: Folder, options: FilterOptions) -> bool:
    return options.clean_excluded and folder.name in EXCLUDED_FOLDERS


PROJECT_FOLDERS: Iterable[str] = []


def _is_project(folder: Folder, options: FilterOptions) -> bool:
    return options.clean_project and folder.name in PROJECT_FOLDERS


def _is_exclude_rule(entry: Folder, options: FilterOptions) -> bool:
    if options.exclude_rules.is_empty():
        return False
    return options.exclude_rules.is_excluded(entry)


def _is_clean_recursive(entry: Folder, options: FilterOptions) -> bool:
    if not options.clean_recursive:
        return False
    return any(folder.name in PROJECT_FOLDERS for folder in entry.folders)


def filter_folder(entry: Folder, options: FilterOptions) -> Optional[Folder]:
    if _is_exclude_rule(entry, options) or _is_clean_recursive(entry, options):
        return Folder(path=entry.path, name=entry.name, files=entry.files, folders=[])
    if _is_excluded(entry, options) or _is_project(entry, options):
        return None
    filtered = []
    for folder in entry.folders:
        cleaned = filter_folder(folder, options)
        if cleaned is None:
            continue
        filtered.append(cleaned)
    return Folder(path=entry.path, name=entry.name, files=entry.files, folders=filtered)


def filter_folders(folders: List[Folder], options: FilterOptions) -> List[Folder]:
    if not options.clean_excluded and not options.clean_project and not options.clean_recursive:
        return folders
    filtered = []
    for folder in folders:
        cleaned = filter_folder(folder, options)
        if cleaned is None:
            continue
        filtered.append(cleaned)
    return filtered


def is_folder_with_name(folder: Folder, names: Sequence[str]) -> bool:
    return folder.name in names


def folders_by_name(folders: Sequence[Folder], names: Sequence[str]) -> List[Folder]:
    filtered = []
    for folder in folders:
        if is_folder_with_name(folder, names):
            filtered.append(folder)
        filtered.extend(folders_by_name(folder.folders, names))
    return filtered


def is_file_with_extensions(file: File, extensions: Sequence[str]) -> bool:
    return file.extension is not None and file.extension in extensions


def _files_by_extension(files: List[File], extensions: Optional[Sequence[str]] = None) -> List[File]:
    if extensions is None or len(extensions) == 0:
        return files
    filtered = []
    for file in files:
        if not is_file_with_extensions(file, extensions):
            continue
        filtered.append(file)
    return filtered


def files_by_extension(folders: Sequence[Folder], extensions: Optional[Sequence[str]] = None) -> List[File]:
    files = []
    for folder in folders:
        files.extend(_files_by_extension(folder.files, extensions))
        files.extend(files_by_extension(folder.folders, extensions))
    return files
