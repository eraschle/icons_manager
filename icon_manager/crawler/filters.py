from collections.abc import Sequence

from icon_manager.crawler.options import FilterOptions
from icon_manager.interfaces.path import File, Folder


def _is_excluded(folder: Folder, options: FilterOptions) -> bool:
    return options.clean_excluded and folder.parent_name in options.excluded_folders


def _is_project(folder: Folder, options: FilterOptions) -> bool:
    return options.clean_project and folder.name in options.project_folders


def _is_exclude_rule(entry: Folder, options: FilterOptions) -> bool:
    if options.exclude.is_empty():
        return False
    return options.exclude.is_excluded(entry)


def _is_clean_recursive(entry: Folder, options: FilterOptions) -> bool:
    if not options.clean_recursive or entry.parent is None:
        return False
    return any(folder.name in options.project_folders for folder in entry.parent.folders)


def filter_folder(entry: Folder, options: FilterOptions) -> Folder | None:
    """Prune ``entry``'s subtree, or drop ``entry`` itself by returning None.

    Three outcomes, which is what the three exclusion mechanisms mean:

    - an exclude rule matches, or a sibling marks a code project: do not
      search inside ``entry``, but ``entry`` itself stays eligible for an
      icon. This is also what ``exclude_folders`` does, since it matches on
      the *parent's* name: the children of an excluded folder are dropped,
      the folder is not.
    - ``entry`` is itself named in ``code_folders``: it is metadata like
      ``.git``, so it is dropped with everything below it.
    - otherwise: recurse, keeping the children that survive.
    """
    if _is_exclude_rule(entry, options) or _is_clean_recursive(entry, options):
        entry.mark_children()
        return entry
    if _is_excluded(entry, options) or _is_project(entry, options):
        entry.mark_and_clean()
        return None
    entry.folders = [kept for folder in entry.folders if (kept := filter_folder(folder, options)) is not None]
    return entry


def filter_folders(folders: list[Folder], options: FilterOptions) -> list[Folder]:
    """Prune every crawled search folder.

    Nothing re-marks a dropped folder here: filter_folder already called
    mark_and_clean() before returning None, so both callers did it twice.
    """
    if not options.clean_excluded and not options.clean_project and not options.clean_recursive:
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
