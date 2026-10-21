from collections.abc import Sequence

from icon_manager.crawler.options import FilterOptions
from icon_manager.interfaces.path import File, Folder
from icon_manager.rules.base import FolderAction


def _starts_project(entry: Folder, options: FilterOptions) -> bool:
    """Whether ``entry`` is a code project, i.e. contains a marker folder.

    Asks about ``entry``'s own children. The predicate this replaces looked
    at ``entry.parent.folders`` - its siblings - so a single ``.venv``
    anywhere on a level stopped the search for every folder on that level,
    and a marker folder always matched it first, which is why ``.git`` used
    to get an icon.
    """
    return any(folder.name in options.project_markers for folder in entry.folders)


def depth_left_at(entry: Folder, options: FilterOptions, inherited: int | None) -> int | None:
    """How many levels may still be searched below ``entry``.

    None means "not inside a project, no limit". ``entry`` starts the
    countdown when it is a project and we are not already inside one.
    """
    if inherited is not None:
        return inherited
    if _starts_project(entry, options):
        return options.project_depth
    return None


def action_for(entry: Folder, options: FilterOptions, depth_left: int | None) -> FolderAction:
    """What should happen to ``entry``, in the order the questions are asked.

    A name in ``skip_names`` wins over everything, then the exclude rules,
    then the project depth.
    """
    if entry.name in options.skip_names:
        return FolderAction.SKIP
    rule_action = options.exclude.action_for(entry)
    if rule_action is not None:
        return rule_action
    if depth_left is not None and depth_left <= 0:
        return FolderAction.LEAF
    return FolderAction.SEARCH


def filter_folder(entry: Folder, options: FilterOptions, inherited_depth: int | None = None) -> Folder | None:
    """Prune ``entry``'s subtree, or drop ``entry`` by returning None.

    Returning None is SKIP: no icon, nothing below it. Returning ``entry``
    with its children marked is LEAF: ``entry`` is still offered to the icon
    rules, nothing below it is.
    """
    depth_left = depth_left_at(entry, options, inherited_depth)
    action = action_for(entry, options, depth_left)
    if action is FolderAction.SKIP:
        entry.mark_and_clean()
        return None
    if action is FolderAction.LEAF:
        entry.mark_children()
        return entry
    child_depth = None if depth_left is None else depth_left - 1
    entry.folders = [
        kept for folder in entry.folders if (kept := filter_folder(folder, options, child_depth)) is not None
    ]
    return entry


def filter_folders(folders: list[Folder], options: FilterOptions) -> list[Folder]:
    """Prune every crawled search folder.

    Nothing re-marks a dropped folder here: filter_folder already called
    mark_and_clean() before returning None, so both callers did it twice.
    """
    if options.filters_nothing():
        return folders
    return [kept for folder in folders if (kept := filter_folder(folder, options)) is not None]


def is_folder_with_name(folder: Folder, names: Sequence[str]) -> bool:
    return folder.name in names


def folders_by_name(folders: Sequence[Folder], names: Sequence[str]) -> list[Folder]:
    filtered = []
    for folder in folders:
        if is_folder_with_name(folder, names):
            filtered.append(folder)
        filtered.extend(folders_by_name(folder.folders, names))
    return filtered


def is_file_with_extensions(file: File, extensions: Sequence[str]) -> bool:
    return file.ext is not None and file.ext in extensions


def _files_by_extension(files: list[File], extensions: Sequence[str] | None = None) -> list[File]:
    if extensions is None or len(extensions) == 0:
        return files
    filtered = []
    for file in files:
        if not is_file_with_extensions(file, extensions):
            continue
        filtered.append(file)
    return filtered


def files_by_extension(folders: Sequence[Folder], extensions: Sequence[str] | None = None) -> list[File]:
    files = []
    for folder in folders:
        files.extend(_files_by_extension(folder.files, extensions))
        files.extend(files_by_extension(folder.folders, extensions))
    return files
