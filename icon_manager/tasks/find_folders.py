import os
from datetime import datetime
from typing import Callable, Iterable, List, Optional

from icon_manager.controller.search import SearchController
from icon_manager.utils.path import get_files, get_folders, get_paths


def duration_message(values: list, searched: str, start: datetime):
    end = datetime.now()
    duration = end - start
    print(f'{duration.total_seconds()} to find {len(values)} {searched}')


class FindOptions:

    @staticmethod
    def default_excluded(value: str) -> bool:
        return SearchController.is_excluded_or_project_folder(value)

    @staticmethod
    def default_stop_recursive(values: Iterable[str]) -> bool:
        return SearchController.is_code_project_folder(values)

    def __init__(self, is_folder_allowed: Optional[Callable[[str], bool]],
                 is_folder_excluded: Optional[Callable[[str], bool]],
                 is_file_allowed: Optional[Callable[[str], bool]],
                 do_stop_recursive: Optional[Callable[[Iterable[str]], bool]]) -> None:
        self.is_folder_allowed = is_folder_allowed
        self.is_folder_excluded = is_folder_excluded
        self.is_file_allowed = is_file_allowed
        self.stop_recursive = do_stop_recursive

    def __is_folder_path_allowed(self, full_path: str) -> bool:
        if self.is_folder_allowed is None:
            return True
        folder_name = os.path.basename(full_path)
        return self.is_folder_allowed(folder_name)

    def __is_folder_path_excluded(self, full_path: str) -> bool:
        if self.is_folder_excluded is None:
            return False
        folder_name = os.path.basename(full_path)
        return self.is_folder_excluded(folder_name)

    def is_folder_path_valid(self, full_path: str) -> bool:
        return (self.__is_folder_path_allowed(full_path)
                and not self.__is_folder_path_excluded(full_path))

    def __not_excluded_folders(self, names: List[str]) -> List[str]:
        if self.is_folder_excluded is None:
            return names
        return [name for name in names if not self.is_folder_excluded(name)]

    def get_not_excluded_folders(self, full_path: str) -> List[str]:
        names = get_folders(full_path)
        return self.__not_excluded_folders(names)

    def __not_excluded_files(self, names: List[str]) -> List[str]:
        return names

    def __allowed_files(self, names: List[str]) -> List[str]:
        if self.is_file_allowed is None:
            return names
        return [name for name in names if self.is_file_allowed(name)]

    def get_valid_files(self, full_path: str) -> List[str]:
        names = get_files(full_path)
        names = self.__not_excluded_files(names)
        return self.__allowed_files(names)

    def stop_recursive_search(self, full_path: str) -> bool:
        if self.stop_recursive is None:
            return False
        folder_names = get_folders(full_path)
        return self.stop_recursive(folder_names)


class FindPathTask:

    def __init__(self, root: str, options: FindOptions) -> None:
        self.root = root
        self.options = options

    def folders_of(self, path: str) -> List[str]:
        folders = []
        if self.options.is_folder_path_valid(path):
            folders.append(path)
        if self.options.stop_recursive_search(path):
            return folders
        folder_names = self.options.get_not_excluded_folders(path)
        for folder_path in get_paths(path, folder_names):
            folders.extend(self.folders_of(folder_path))
        return folders

    def folders(self) -> List[str]:
        start = datetime.now()
        folders = self.folders_of(self.root)
        duration_message(folders, 'folders', start)
        return folders

    def get_valid_file_paths(self, path: str) -> List[str]:
        files = self.options.get_valid_files(path)
        return get_paths(path, files)

    def files_of(self, path: str) -> List[str]:
        files = self.get_valid_file_paths(path)
        if self.options.stop_recursive_search(path):
            return files
        folder_names = self.options.get_not_excluded_folders(path)
        for folder_path in get_paths(path, folder_names):
            files.extend(self.files_of(folder_path))
        return files

    def files(self) -> List[str]:
        start = datetime.now()
        files = self.files_of(self.root)
        duration_message(files, 'files', start)
        return files
