import logging
import os
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from icon_manager.crawler.filters import files_by_extension, is_file_with_extensions
from icon_manager.interfaces.path import File, Folder, IconSearchFolder, SearchFolder

log = logging.getLogger(__name__)


def crawle_folder(path: str, parent: Folder | None) -> Folder:
    """Read ``path`` and everything below it into a Folder tree."""
    current = Folder.from_path(path, parent)
    for entry in os.scandir(path):
        if entry.is_dir():
            current.folders.append(crawle_folder(entry.path, current))
        else:
            current.files.append(File.from_path(entry.path, current))
    return current


def crawling_folders(roots: Sequence[SearchFolder]) -> list[Folder]:
    """Crawl every root sequentially."""
    return [crawle_folder(root.path, None) for root in roots]


def async_crawling_folders(name: str, roots: Sequence[SearchFolder]) -> list[Folder]:
    """Crawl every root, parallelising over each root's direct children.

    One pool per root, each task crawling one child subtree into its own
    Folder; the results are attached here, on the calling thread. The
    previous version nested a pool inside a pool for every folder of the
    first two levels and let several threads append to the same lists, which
    only happened to work because of the GIL.
    """
    return [_crawle_root(name, root) for root in roots]


def _crawle_root(name: str, root: SearchFolder) -> Folder:
    current = Folder.from_path(root.path, None)
    children = list(os.scandir(root.path))
    folders = [entry for entry in children if entry.is_dir()]
    current.files = [File.from_path(entry.path, current) for entry in children if not entry.is_dir()]
    if not folders:
        return current
    prefix = f"{name} crawling {root.path}"
    with ThreadPoolExecutor(thread_name_prefix=prefix, max_workers=min(len(folders), 32)) as executor:
        tasks = {executor.submit(crawle_folder, entry.path, current): entry for entry in folders}
        for future in as_completed(tasks):
            entry = tasks[future]
            try:
                current.folders.append(future.result())
            except Exception as exc:
                log.error("%r Exception: %s", entry.path, exc)
    return current


def _group_by_extension(files: Iterable[File], extensions: Sequence[str]) -> dict[str, list[File]]:
    grouped: dict[str, list[File]] = {}
    for file in files:
        if file.ext is None or not is_file_with_extensions(file, extensions):
            continue
        grouped.setdefault(file.ext, []).append(file)
    return grouped


def crawling_icons(root: SearchFolder, extensions: Sequence[str]) -> dict[str, list[File]]:
    """The icon library's files, grouped by extension (``ico`` and ``json``)."""
    folder = crawle_folder(root.path, None)
    files = files_by_extension([folder], extensions)
    return _group_by_extension(files, extensions)


__all__ = [
    "IconSearchFolder",
    "async_crawling_folders",
    "crawle_folder",
    "crawling_folders",
    "crawling_icons",
]
