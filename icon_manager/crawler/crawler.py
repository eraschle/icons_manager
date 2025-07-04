import concurrent.futures
import os
from collections.abc import Iterable, Sequence

from icon_manager.crawler.filters import files_by_extension, is_file_with_extensions
from icon_manager.helpers.path import crawle_folder
from icon_manager.interfaces.path import File, Folder, IconSearchFolder, SearchFolder


def _crawling(root: SearchFolder) -> Folder:
    current = Folder.from_path(root.path, None)
    for entry in os.scandir(root.path):
        if entry.is_dir():
            current.folders.append(crawle_folder(entry, current))
        else:
            current.files.append(File.from_path(entry.path, current))
    return current


# @crawler_result(message='Crawler found', log_start='SYNC crawler started')
def crawling_folders(roots: Sequence[IconSearchFolder]) -> list[Folder]:
    folders = []
    for root in roots:
        folders.append(_crawling(root))
    return folders


# @crawler_result(message='Crawler found', log_start='ASYNC_crawler started')
def async_crawling_folders(roots: Sequence[IconSearchFolder]) -> list[Folder]:
    folders = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        task = {executor.submit(_crawling, root): root for root in roots}
        for future in concurrent.futures.as_completed(task):
            root_folder = task[future]
            try:
                folder = future.result()
                folders.append(folder)
            except Exception as exc:
                print("%r Exception: %s" % (root_folder.path, exc))
    return folders


def _group_by_extension(files: Iterable[File], extensions: Sequence[str]) -> dict[str, list[File]]:
    grouped: dict[str, list[File]] = {}
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
