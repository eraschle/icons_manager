import concurrent.futures
import os
from typing import Dict, Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.crawler.filters import (files_by_extension,
                                          is_file_with_extensions)
from icon_manager.interfaces.path import (File, Folder, IconSearchFolder,
                                          SearchFolder,)


def crawle_folder(entry: os.DirEntry, parent: Optional[Folder]) -> Folder:
    current = Folder.from_path(entry.path, parent)
    for elem in os.scandir(entry.path):
        if elem.is_dir():
            current.folders.append(crawle_folder(elem, current))
        else:
            current.files.append(File.from_path(elem.path, current))
    return current


def crawling_entry(entry: os.DirEntry, current: Folder) -> Folder:
    if entry.is_dir():
        current.folders.append(crawle_folder(entry, current))
    else:
        current.files.append(File.from_path(entry.path, current))
    return current


def async_crawle_folder(config: UserConfig, entry: os.DirEntry, parent: Optional[Folder]) -> Folder:
    current = Folder.from_path(entry.path, parent)
    prefix = f'{config.name} Crawling {entry.path}'
    with concurrent.futures.ThreadPoolExecutor(thread_name_prefix=prefix) as executor:
        task = {executor.submit(crawling_entry, entry, current): entry for entry in os.scandir(entry.path)}
        for future in concurrent.futures.as_completed(task):
            root_folder = task[future]
            try:
                current = future.result()
            except Exception as exc:
                print('%r Exception: %s' % (root_folder.path, exc))
    return current


def _crawling_root(config: UserConfig, entry: os.DirEntry, current: Folder) -> Folder:
    if entry.is_dir():
        current.folders.append(async_crawle_folder(config, entry, current))
    else:
        current.files.append(File.from_path(entry.path, current))
    return current


def _async_crawling(config: UserConfig, root: SearchFolder) -> Folder:
    current = Folder.from_path(root.path, None)
    prefix = f'{config.name} Crawling {root.path}'
    with concurrent.futures.ThreadPoolExecutor(thread_name_prefix=prefix) as executor:
        task = {executor.submit(_crawling_root, config, entry, current)
                                : entry for entry in os.scandir(root.path)}
        for future in concurrent.futures.as_completed(task):
            root_folder = task[future]
            try:
                current = future.result()
            except Exception as exc:
                print('%r Exception: %s' % (root_folder.path, exc))
    return current


def async_crawling_folders(config: UserConfig, roots: Sequence[IconSearchFolder]) -> List[Folder]:
    folders = []
    prefix = f'Crawler {config.name}'
    with concurrent.futures.ThreadPoolExecutor(thread_name_prefix=prefix) as executor:
        task = {executor.submit(_async_crawling, config,
                                root): root for root in roots}
        for future in concurrent.futures.as_completed(task):
            root_folder = task[future]
            try:
                folder = future.result()
                folders.append(folder)
            except Exception as exc:
                print('%r Exception: %s' % (root_folder.path, exc))
    return folders


def _crawling(root: SearchFolder) -> Folder:
    current = Folder.from_path(root.path, None)
    for entry in os.scandir(root.path):
        if entry.is_dir():
            current.folders.append(crawle_folder(entry, current))
        else:
            current.files.append(File.from_path(entry.path, current))
    return current


def crawling_folders(roots: Sequence[IconSearchFolder]) -> List[Folder]:
    folders = []
    for root in roots:
        folders.append(_crawling(root))
    return folders


def _group_by_extension(files: Iterable[File], extensions: Sequence[str]) -> Dict[str, List[File]]:
    grouped: Dict[str, List[File]] = {}
    for file in files:
        if file.ext is None:
            continue
        if not is_file_with_extensions(file, extensions):
            continue
        if file.ext not in grouped:
            grouped[file.ext] = []
        grouped[file.ext].append(file)
    return grouped


def crawling_icons(root: SearchFolder, extensions: Sequence[str]) -> dict[str, list[File]]:
    folder = _crawling(root)
    files = files_by_extension([folder], extensions)
    return _group_by_extension(files, extensions)
