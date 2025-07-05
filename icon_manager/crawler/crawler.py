import concurrent.futures
import os
from typing import Dict, Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.crawler.filters import (files_by_extension,
                                          is_file_with_extensions)
from icon_manager.interfaces.path import (File, Folder, IconSearchFolder,
                                          SearchFolder)


def crawle_folder(entry: os.DirEntry, parent: Optional[Folder]) -> Folder:
    """
    Recursively scans a directory entry and builds a Folder object tree.
    
    Creates a Folder for the given directory entry, then traverses its contents. Subdirectories are recursively processed and added to the Folder's folders list, while files are added to the files list. Returns the fully populated Folder representing the directory and its contents.
    """
    current = Folder.from_path(entry.path, parent)
    for elem in os.scandir(entry.path):
        if elem.is_dir():
            current.folders.append(crawle_folder(elem, current))
        else:
            current.files.append(File.from_path(elem.path, current))
    return current


def crawling_entry(entry: os.DirEntry, current: Folder) -> Folder:
    """
    Adds a directory or file entry to the given Folder, recursively crawling subdirectories.
    
    If the entry is a directory, its contents are recursively scanned and added as a subfolder. If the entry is a file, it is added to the folder's files list.
    
    Returns:
        Folder: The updated Folder with the new entry added.
    """
    if entry.is_dir():
        current.folders.append(crawle_folder(entry, current))
    else:
        current.files.append(File.from_path(entry.path, current))
    return current


def async_crawle_folder(config: UserConfig, entry: os.DirEntry, parent: Optional[Folder]) -> Folder:
    """
    Recursively crawls a directory and its contents asynchronously, building a Folder object tree.
    
    Each entry in the directory is processed concurrently using a thread pool. Subdirectories and files are added to the Folder structure. Exceptions during processing are caught and printed. Returns the populated Folder representing the directory and its contents.
    """
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
    """
    Processes a directory entry as part of asynchronous folder crawling, adding its contents to the given Folder.
    
    If the entry is a directory, recursively crawls it and appends the resulting Folder to the current folder's subfolders. If the entry is a file, creates a File object and appends it to the current folder's files.
    
    Returns:
        Folder: The updated Folder with the new entry added.
    """
    if entry.is_dir():
        current.folders.append(async_crawle_folder(config, entry, current))
    else:
        current.files.append(File.from_path(entry.path, current))
    return current


def _async_crawling(config: UserConfig, root: SearchFolder) -> Folder:
    """
    Asynchronously crawls a root directory and its contents using a thread pool, building and returning a Folder object representing the directory tree.
    
    Parameters:
        root (SearchFolder): The root directory to crawl.
    
    Returns:
        Folder: The populated Folder object representing the crawled directory and its subdirectories.
    """
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
    """
    Asynchronously crawls multiple root folders in parallel and returns their directory structures.
    
    Each root folder is processed concurrently using a thread pool, building a `Folder` object tree for each. Exceptions encountered during crawling are caught and printed, and do not interrupt processing of other roots.
    
    Returns:
        List[Folder]: A list of `Folder` objects representing the crawled directory structures for each root.
    """
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
    """
    Recursively scans the given root directory and builds a Folder object tree representing its structure.
    
    Returns:
        Folder: The root Folder object containing all subfolders and files found under the specified root directory.
    """
    current = Folder.from_path(root.path, None)
    for entry in os.scandir(root.path):
        if entry.is_dir():
            current.folders.append(crawle_folder(entry, current))
        else:
            current.files.append(File.from_path(entry.path, current))
    return current


def crawling_folders(roots: Sequence[IconSearchFolder]) -> List[Folder]:
    """
    Synchronously crawls multiple root folders and returns their directory structures as Folder objects.
    
    Parameters:
        roots (Sequence[IconSearchFolder]): The root folders to crawl.
    
    Returns:
        List[Folder]: A list of Folder objects representing the directory trees of each root.
    """
    folders = []
    for root in roots:
        folders.append(_crawling(root))
    return folders


def _group_by_extension(files: Iterable[File], extensions: Sequence[str]) -> Dict[str, List[File]]:
    """
    Group files by their extension, including only those with extensions in the provided list.
    
    Parameters:
        files: An iterable of File objects to group.
        extensions: A sequence of file extensions to include in the grouping.
    
    Returns:
        A dictionary mapping each extension to a list of File objects with that extension.
    """
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


def crawling_icons(root: SearchFolder, extensions: Sequence[str]) -> Dict[str, List[File]]:
    folder = _crawling(root)
    files = files_by_extension([folder], extensions)
    return _group_by_extension(files, extensions)
