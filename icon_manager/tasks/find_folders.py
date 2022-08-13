from typing import Callable, Iterable, List, Optional
from icon_manager.controller.search import SearchController

from icon_manager.utils.path import get_files, get_folders, get_paths


class FindOptions:
    def __init__(self, is_folder_allowed: Optional[Callable[[str], bool]] = None,
                 is_file_allowed: Optional[Callable[[str], bool]] = None,
                 do_stop_recursive: Optional[Callable[[Iterable[str]], bool]] = None) -> None:
        self.is_folder_allowed = is_folder_allowed
        self.is_file_allowed = is_file_allowed
        self.stop_recursive = do_stop_recursive

    def get_allowed_folders(self, names: Iterable[str]) -> Iterable[str]:
        if self.is_folder_allowed is None:
            return names
        return [name for name in names if self.is_folder_allowed(name)]

    def get_allowed_files(self, names: Iterable[str]) -> Iterable[str]:
        if self.is_file_allowed is None:
            return names
        return [name for name in names if self.is_file_allowed(name)]

    def stop_recursive_search(self, names: Iterable[str]) -> bool:
        if self.stop_recursive is None:
            return False
        return self.stop_recursive(names)


class FindPathTask:

    def __init__(self, root: str, options: FindOptions) -> None:
        self.root = root
        self.options = options

    def folder_names_of(self, path: str) -> Iterable[str]:
        folders = get_folders(path)
        return self.options.get_allowed_folders(folders)

    def folders_of(self, path: str) -> Iterable[str]:
        folders = [path]
        folder_names = self.folder_names_of(path)
        if self.options.stop_recursive_search(folder_names):
            return folders
        for folder_path in get_paths(path, folder_names):
            folders.extend(self.folders_of(folder_path))
        return folders

    def folders(self) -> Iterable[str]:
        return self.folders_of(self.root)

    def file_paths_of(self, path: str) -> List[str]:
        files = get_files(path)
        files = self.options.get_allowed_files(files)
        return get_paths(path, files)

    def files_of(self, path: str) -> Iterable[str]:
        files = self.file_paths_of(path)
        folder_names = self.folder_names_of(path)
        if self.options.stop_recursive_search(folder_names):
            return files
        for folder_path in get_paths(path, folder_names):
            files.extend(self.files_of(folder_path))
        return files

    def files(self) -> Iterable[str]:
        return self.files_of(self.root)
