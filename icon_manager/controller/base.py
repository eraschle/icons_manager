from abc import ABC
from typing import Generic, Iterable, List, Type, TypeVar

from icon_manager.models.path import FileModel, FolderModel
from icon_manager.tasks.find_folders import (File, FindOptions, FindPathTask,
                                             Folder)

TFile = TypeVar('TFile', bound=FileModel)
TFolder = TypeVar('TFolder', bound=FolderModel)


class BaseController(ABC, Generic[TFile, TFolder]):
    def __init__(self, full_path: str, file_type: Type[TFile] = FileModel,
                 folder_type: Type[TFolder] = FolderModel) -> None:
        self.full_path = full_path
        self.file_type = file_type
        self.folder_type = folder_type
        self.__searched_for_files_and_folders: bool = False
        self.__folders: List[TFolder] = []
        self.__files: List[TFile] = []

    def get_find_options(self) -> FindOptions:
        return FindOptions(add_default=True,
                           folder_allowed=self.folder_type.is_model,
                           file_allowed=self.file_type.is_model)

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        self.__files.extend(self.get_files(folders, files))
        self.__folders.extend(self.get_folders(folders, files))

    def search_for_folders_and_files(self, search_again: bool = False) -> None:
        if self.__searched_for_files_and_folders and not search_again:
            return
        find_task = FindPathTask(self.full_path, self.get_find_options(),
                                 self.on_found_folders_and_files)
        find_task.find_folder_and_files()
        self.__searched_for_files_and_folders = True

    def files(self, search_again: bool = False) -> Iterable[TFile]:
        self.search_for_folders_and_files(search_again)
        return self.__files

    def get_files(self, _: Iterable[Folder], files: Iterable[File]) -> Iterable[TFile]:
        return [self.file_type(file.full_path) for file in files if self.file_type.is_model(file.full_path)]

    def folders(self, search_again: bool = False) -> Iterable[TFolder]:
        self.search_for_folders_and_files(search_again)
        return self.__folders

    def get_folders(self, folders: Iterable[Folder], _: Iterable[File]) -> Iterable[TFolder]:
        return [self.folder_type(folder.full_path) for folder in folders if self.file_type.is_model(folder.full_path)]
