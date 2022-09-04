import concurrent.futures
import os
from typing import Dict, Iterable, List, Sequence

from icon_manager.crawler.filters import (files_by_extension,
                                          is_file_with_extensions)
from icon_manager.helpers.path import File, Folder, crawle_folder, create_file
from icon_manager.interfaces.path import IconSearchFolder, SearchFolder


def _crawling(root: SearchFolder) -> Folder:
    files = []
    folders = []
    path = root.path
    for entry in os.scandir(path):
        if entry.is_dir():
            folders.append(crawle_folder(entry))
        else:
            files.append(create_file(entry.path, entry.name))
    return Folder(path=path, name=root.name, files=files, folders=folders)


def crawling_search_folders(roots: Sequence[IconSearchFolder]) -> List[Folder]:
    folders = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the load operations and mark each future with its URL
        task = {executor.submit(_crawling, root): root for root in roots}
        for future in concurrent.futures.as_completed(task):
            root_folder = task[future]
            try:
                folder = future.result()
                folders.append(folder)
            except Exception as exc:
                print('%r Exception: %s' % (root_folder.path, exc))
    return folders


def _group_by_extension(files: Iterable[File], extensions: Sequence[str]) -> Dict[str, List[File]]:
    grouped: Dict[str, List[File]] = {}
    for file in files:
        if file.extension is None:
            continue
        if not is_file_with_extensions(file, extensions):
            continue
        if file.extension not in grouped:
            grouped[file.extension] = []
        grouped[file.extension].append(file)

    return grouped


def crawling_icons(root: SearchFolder, extensions: Sequence[str]) -> Dict[str, List[File]]:
    folder = _crawling(root)
    files = files_by_extension([folder], extensions)
    return _group_by_extension(files, extensions)
