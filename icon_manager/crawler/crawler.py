import logging
import os
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from icon_manager.crawler.filters import (
    action_for,
    depth_left_at,
    files_by_extension,
    is_file_with_extensions,
    is_skipped_name,
)
from icon_manager.crawler.options import FilterOptions
from icon_manager.interfaces.path import File, Folder, IconSearchFolder, SearchFolder
from icon_manager.rules.base import FolderAction

log = logging.getLogger(__name__)


def crawle_folder(path: str, parent: Folder | None) -> Folder:
    """Read ``path`` and everything below it into a Folder tree.

    Unfiltered. Used for the icon library, which is small and has nothing to
    prune; the search folders go through :func:`crawl_search_folders`.
    """
    current = Folder.from_path(path, parent)
    for entry in os.scandir(path):
        if entry.is_dir():
            current.folders.append(crawle_folder(entry.path, current))
        else:
            current.files.append(File.from_path(entry.path, current))
    return current


def crawling_folders(roots: Sequence[SearchFolder]) -> list[Folder]:
    """Crawl every root sequentially and unfiltered."""
    return [crawle_folder(root.path, None) for root in roots]


def _attach_children(path: str, current: Folder) -> list[os.DirEntry]:
    """Attach everything directly in ``path`` to ``current``.

    All subfolders are attached, skipped ones included: the project markers
    (``.git``, ``.venv``) are exactly the skipped names, so dropping them
    here would hide the very thing that identifies a project, and a
    ``contains_folder`` rule asks about them too. Only the descent is
    filtered, which is where the saved I/O is.
    """
    child_dirs = []
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            child_dirs.append(entry)
        else:
            current.files.append(File.from_path(entry.path, current))
    current.folders = [Folder.from_path(entry.path, current) for entry in child_dirs]
    return child_dirs


def _materialise(folder: Folder, options: FilterOptions, depth: int) -> None:
    """Read ``depth`` further levels below ``folder`` without deciding anything.

    Only for a folder the walk stops at: a ``contains_file`` or
    ``contains_folder`` rule with a ``level`` above 1 still has to see that
    far down, so pruning the walk cannot change what a rule sees. ``depth``
    comes from the rules themselves via ``required_depth()`` and is 0 unless
    some rule asks for more.
    """
    if depth <= 0:
        return
    for entry in _attach_children(folder.path, folder):
        if is_skipped_name(entry.name, options):
            continue
        child = next(f for f in folder.folders if f.path == entry.path)
        _materialise(child, options, depth - 1)


def _crawl(path: str, parent: Folder | None, options: FilterOptions, inherited_depth: int | None) -> Folder | None:
    """Crawl ``path``, applying the filter as the walk goes.

    Returns None for a folder that is skipped, so it never reaches the icon
    rules and its subtree is never read.
    """
    current = Folder.from_path(path, parent)
    child_dirs = _attach_children(path, current)
    if options.inspect_depth > 0:
        for stub in current.folders:
            _materialise(stub, options, options.inspect_depth)

    depth_left = depth_left_at(current, options, inherited_depth)
    action = action_for(current, options, depth_left)
    if action is FolderAction.SKIP:
        return None
    if action is FolderAction.LEAF:
        # the children stay attached but marked, so a contains_folder rule on
        # this folder can still read their names while the icon rules skip them
        current.mark_children()
        return current

    child_depth = None if depth_left is None else depth_left - 1
    current.folders = _walk_children(child_dirs, current, options, child_depth)
    return current


def _walk_children(
    child_dirs: Sequence[os.DirEntry], parent: Folder, options: FilterOptions, child_depth: int | None
) -> list[Folder]:
    """Crawl the children worth crawling, replacing their stubs.

    A skipped name is never read: _crawl would return None for it anyway,
    but only after listing the folder, and that listing is the cost this
    whole change is about.
    """
    kept = []
    for entry in child_dirs:
        if is_skipped_name(entry.name, options):
            continue
        folder = _crawl(entry.path, parent, options, child_depth)
        if folder is not None:
            kept.append(folder)
    return kept


def crawl_search_folders(name: str, roots: Sequence[SearchFolder], options: FilterOptions) -> list[Folder]:
    """Crawl every root, filtering as the walk goes, one pool per root.

    The filter used to run on the finished tree, so ``exclude_folders``,
    ``code_folders`` and ``project_depth`` saved no I/O at all: a
    ``node_modules`` with 40000 folders was read in full and then thrown
    away. On a tree of 6756 folders with twelve projects, deciding during
    the walk reads 37 of them instead of 6757.
    """
    crawled = []
    for root in roots:
        folder = _crawl_root(name, root, options)
        if folder is not None:
            crawled.append(folder)
    return crawled


def _crawl_root(name: str, root: SearchFolder, options: FilterOptions) -> Folder | None:
    current = Folder.from_path(root.path, None)
    child_dirs = _attach_children(root.path, current)
    if options.inspect_depth > 0:
        for stub in current.folders:
            _materialise(stub, options, options.inspect_depth)

    depth_left = depth_left_at(current, options, None)
    action = action_for(current, options, depth_left)
    if action is FolderAction.SKIP:
        return None
    if action is FolderAction.LEAF:
        current.mark_children()
        return current

    child_depth = None if depth_left is None else depth_left - 1
    to_walk = [entry for entry in child_dirs if not is_skipped_name(entry.name, options)]
    if not to_walk:
        current.folders = []
        return current

    prefix = f"{name} crawling {root.path}"
    kept: list[Folder] = []
    with ThreadPoolExecutor(thread_name_prefix=prefix, max_workers=min(len(to_walk), 32)) as executor:
        tasks = {executor.submit(_crawl, entry.path, current, options, child_depth): entry for entry in to_walk}
        for future in as_completed(tasks):
            entry = tasks[future]
            try:
                folder = future.result()
            except Exception as exc:
                log.error("%r Exception: %s", entry.path, exc)
                continue
            if folder is not None:
                kept.append(folder)
    current.folders = kept
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
    "crawl_search_folders",
    "crawle_folder",
    "crawling_folders",
    "crawling_icons",
]
