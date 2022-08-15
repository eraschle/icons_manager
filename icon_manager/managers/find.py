import os
from collections import namedtuple
from datetime import datetime
from typing import Callable, Iterable, List, Optional, Tuple

from icon_manager.controller.search import SearchController
from icon_manager.utils.path import get_files, get_folders, get_paths


def duration_message(values: list, searched: str, start: datetime):
    end = datetime.now()
    duration = end - start
    print(f'{duration.total_seconds()} to find {len(values)} {searched}')


File = namedtuple('File', ['full_path', 'name'])
Folder = namedtuple('Folder', ['full_path', 'name'])


class FindOptions:

    @staticmethod
    def no_file_allowed(_: str) -> bool:
        return False

    def __init__(self, add_default: bool,
                 folder_allowed: Optional[Callable[[str], bool]] = None,
                 folder_excluded: Optional[Callable[[str], bool]] = None,
                 file_allowed: Optional[Callable[[str], bool]] = None,
                 stop_search: Optional[Callable[[Iterable[str]], bool]] = None) -> None:
        self.__folder_allowed: List[Callable[[str], bool]] = []
        self.__folder_excluded: List[Callable[[str], bool]] = []
        self.__file_allowed: List[Callable[[str], bool]] = []
        self.__stop_recursive: List[Callable[[Iterable[str]], bool]] = []
        self.__add_initial_callables(folder_allowed, folder_excluded,
                                     file_allowed, stop_search)
        if add_default:
            self.add_default_callables()

    def add_default_callables(self):
        self.__folder_excluded.append(SearchController.is_folder_excluded)
        self.__folder_excluded.append(SearchController.is_project_folder)
        self.__stop_recursive.append(SearchController.is_project_folder)

    def __add_initial_callables(self, is_folder_allowed: Optional[Callable[[str], bool]],
                                is_folder_excluded: Optional[Callable[[str], bool]],
                                is_file_allowed: Optional[Callable[[str], bool]],
                                do_stop_recursive: Optional[Callable[[Iterable[str]], bool]]):
        if is_folder_allowed is not None:
            self.__folder_allowed.append(is_folder_allowed)
        if is_folder_excluded is not None:
            self.__folder_excluded.append(is_folder_excluded)
        if is_file_allowed is not None:
            self.__file_allowed.append(is_file_allowed)
        if do_stop_recursive is not None:
            self.__stop_recursive.append(do_stop_recursive)


# region CALLABLES

    def add_folder_allowed(self, folder_allowed: Callable[[str], bool]):
        if folder_allowed is None:
            return
        self.__folder_allowed.append(folder_allowed)

    def reset_folder_allowed(self, folder_allowed: Callable[[str], bool]):
        self.clear_folder_allowed()
        self.add_folder_allowed(folder_allowed)

    def clear_folder_allowed(self):
        self.__folder_allowed.clear()

    def add_folder_excluded(self, folder_excluded: Callable[[str], bool]):
        if folder_excluded is None:
            return
        self.__folder_excluded.append(folder_excluded)

    def reset_folder_excluded(self, folder_excluded: Callable[[str], bool]):
        self.clear_folder_excluded()
        self.add_folder_excluded(folder_excluded)

    def clear_folder_excluded(self):
        self.__folder_excluded.clear()

    def add_file_allowed(self, file_allowed: Callable[[str], bool]):
        if file_allowed is None:
            return
        self.__file_allowed.append(file_allowed)

    def reset_file_allowed(self, file_allowed: Callable[[str], bool]):
        self.clear_file_allowed()
        self.add_file_allowed(file_allowed)

    def clear_file_allowed(self):
        self.__file_allowed.clear()

    def add_stop_recursive(self, stop_recursive: Callable[[Iterable[str]], bool]):
        if stop_recursive is None:
            return
        self.__stop_recursive.append(stop_recursive)

    def reset_stop_recursive(self, stop_recursive: Callable[[Iterable[str]], bool]):
        self.clear_stop_recursive()
        self.add_stop_recursive(stop_recursive)

    def clear_stop_recursive(self):
        self.__stop_recursive.clear()


# endregion


    def __is_folder_name_allowed(self, name: str) -> bool:
        if len(self.__folder_allowed) == 0:
            return True
        return any(is_allowed(name) for is_allowed in self.__folder_allowed)

    def __is_folder_path_allowed(self, full_path: str) -> bool:
        if len(self.__folder_allowed) == 0:
            return True
        folder_name = os.path.basename(full_path)
        return self.__is_folder_name_allowed(folder_name)

    def get_allowed_folder_names(self, folder_names: Iterable[str]) -> Iterable[str]:
        if len(self.__folder_allowed) == 0:
            return folder_names
        return [name for name in folder_names if self.__is_folder_name_allowed(name)]

    def __is_excluded_folder_name(self, name: str) -> bool:
        if len(self.__folder_excluded) == 0:
            return False
        return any(is_excluded(name) for is_excluded in self.__folder_excluded)

    def __is_folder_path_excluded(self, full_path: str) -> bool:
        folder_name = os.path.basename(full_path)
        return self.__is_excluded_folder_name(folder_name)

    def is_folder_path_valid(self, full_path: str) -> bool:
        return (self.__is_folder_path_allowed(full_path)
                and not self.__is_folder_path_excluded(full_path))

    def get_not_excluded_folder_names(self, folder_names: Iterable[str]) -> Iterable[str]:
        if len(self.__folder_excluded) == 0:
            return folder_names
        return [name for name in folder_names if not self.__is_excluded_folder_name(name)]

    def get_valid_folder_names(self, full_path: str) -> Iterable[str]:
        names = get_folders(full_path)
        names = self.get_not_excluded_folder_names(names)
        return self.get_allowed_folder_names(names)

    def __not_excluded_file_names(self, names: Iterable[str]) -> Iterable[str]:
        return names

    def __is_allowed_file_name(self, name: str) -> bool:
        return any(is_allowed(name) for is_allowed in self.__file_allowed)

    def __allowed_file_names(self, names: Iterable[str]) -> Iterable[str]:
        if len(self.__file_allowed) == 0:
            return names
        return [name for name in names if self.__is_allowed_file_name(name)]

    def get_valid_file_names(self, full_path: str) -> Iterable[str]:
        names = get_files(full_path)
        names = self.__not_excluded_file_names(names)
        return self.__allowed_file_names(names)

    def stop_recursive_search(self, path: str) -> bool:
        if len(self.__stop_recursive) == 0:
            return False
        names = get_folders(path)
        return any(do_stop(names) for do_stop in self.__stop_recursive)


class FindManager:

    def __init__(self, root: str, options: FindOptions,
                 on_found: Optional[Callable[[Iterable[Folder], Iterable[File]], None]] = None) -> None:
        self.root = root
        self.options = options
        self.on_found = on_found

    def get_valid_files(self, full_path: str) -> List[File]:
        names = self.options.get_valid_file_names(full_path)
        paths = get_paths(full_path, names)
        return [File(name=name, full_path=path) for name, path in zip(names, paths)]

    def get_valid_folders(self, full_path: str) -> List[Folder]:
        names = self.options.get_valid_folder_names(full_path)
        paths = get_paths(full_path, names)
        return [Folder(name=name, full_path=path) for name, path in zip(names, paths)]

    def __fire_on_found(self, folders: Iterable[Folder], files: Iterable[File]):
        if self.on_found is None:
            return
        self.on_found(folders, files)

    def walk_tree(self, full_path: str) -> Tuple[Iterable[Folder], Iterable[File]]:
        if self.options.stop_recursive_search(full_path):
            return [], []
        folders = self.get_valid_folders(full_path)
        files = self.get_valid_files(full_path)
        self.__fire_on_found(folders, files)
        folder_names = get_folders(full_path)
        folder_names = self.options.get_not_excluded_folder_names(folder_names)
        for folder_path in get_paths(full_path, folder_names):
            sub_folders, sub_files = self.walk_tree(folder_path)
            folders.extend(sub_folders)
            files.extend(sub_files)
        return folders, files

    def find_folder_and_files(self) -> Tuple[Iterable[Folder], Iterable[File]]:
        folders: List[Folder] = []
        files: List[File] = []
        if self.options.is_folder_path_valid(self.root):
            name = os.path.basename(self.root)
            folders.append(Folder(full_path=self.root, name=name))
            files = self.get_valid_files(self.root)
            self.__fire_on_found(folders, files)
        sub_folders, sub_files = self.walk_tree(self.root)
        folders.extend(sub_folders)
        files.extend(sub_files)
        return folders, files
