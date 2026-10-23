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


def is_skipped_name(name: str, options: FilterOptions) -> bool:
    """Whether a folder of this name is skipped whatever it contains.

    Answerable from the name alone, which is what lets the crawler decide
    before it reads the folder at all.
    """
    return name in options.skip_names


def action_for(entry: Folder, options: FilterOptions, depth_left: int | None) -> FolderAction:
    """What should happen to ``entry``, in the order the questions are asked.

    A name in ``skip_names`` wins over everything, then the exclude rules,
    then the project depth.

    ``entry`` must have its direct children attached, since both the exclude
    rules and the project detection may ask about them.
    """
    if is_skipped_name(entry.name, options):
        return FolderAction.SKIP
    rule_action = options.exclude.action_for(entry)
    if rule_action is not None:
        return rule_action
    if depth_left is not None and depth_left <= 0:
        return FolderAction.LEAF
    return FolderAction.SEARCH


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
