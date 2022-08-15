from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Type, TypeVar

from icon_manager.models.path import FileModel, FolderModel
from icon_manager.tasks.find_folders import (File, FindOptions, FindPathTask,
                                             Folder)

TFile = TypeVar('TFile', bound=FileModel)
TFolder = TypeVar('TFolder', bound=FolderModel)


class BaseController(ABC):
    def __init__(self) -> None:
        self.__searched_for_files_and_folders: bool = False

    @abstractmethod
    def get_find_options(self) -> FindOptions:
        ...

    def get_find_task(self, search_path: str) -> FindPathTask:
        return FindPathTask(search_path, self.get_find_options(),
                            self.on_found_folders_and_files)

    @abstractmethod
    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        ...

    def search_for_folders_and_files(self, search_path: str, search_again: bool = False) -> None:
        if self.__searched_for_files_and_folders and not search_again:
            return
        find_task = self.get_find_task(search_path)
        find_task.find_folder_and_files()
        self.__searched_for_files_and_folders = True


class FileBaseController(BaseController, Generic[TFile]):
    def __init__(self, full_path: str, file_type: Type[TFile]) -> None:
        super().__init__()
        self.full_path = full_path
        self.file_type = file_type
        self.files: List[TFile] = []

    def get_find_options(self) -> FindOptions:
        return FindOptions(add_default=True,
                           file_allowed=self.file_type.is_model)

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        self.files.extend(self.create_files(folders, files))

    def create_files(self, _: Iterable[Folder], files: Iterable[File]) -> Iterable[TFile]:
        return [self.file_type(file.full_path) for file in files if self.file_type.is_model(file.full_path)]

    def get_files(self, search_again: bool = False) -> Iterable[TFile]:
        self.search_for_folders_and_files(self.full_path, search_again)
        return self.files


class FolderBaseController(BaseController, Generic[TFolder]):
    def __init__(self, full_path: str, folder_type: Type[TFolder]) -> None:
        super().__init__()
        self.full_path = full_path
        self.folder_type = folder_type
        self.folders: List[TFolder] = []

    def get_find_options(self) -> FindOptions:
        return FindOptions(add_default=True,
                           folder_allowed=self.folder_type.is_model,
                           file_allowed=FindOptions.no_file_allowed)

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        self.folders.extend(self.create_folders(folders, files))

    def create_folders(self, folders: Iterable[Folder], _: Iterable[File]) -> Iterable[TFolder]:
        return [self.folder_type(folder.full_path) for folder in folders if self.folder_type.is_model(folder.full_path)]

    def get_folders(self, search_again: bool = False) -> Iterable[TFolder]:
        self.search_for_folders_and_files(self.full_path, search_again)
        return self.folders
