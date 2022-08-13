from abc import ABC
from typing import Generic, Iterable, Type, TypeVar
from icon_manager.controller.search import SearchController

from icon_manager.models.path import FileModel
from icon_manager.tasks.find_folders import FindOptions, FindPathTask

TFile = TypeVar('TFile', bound=FileModel)


class BaseController(ABC, Generic[TFile]):
    def __init__(self, full_path: str, file_type: Type[TFile]) -> None:
        self.full_path = full_path
        self.file_type = file_type

    def get_content(self, paths: Iterable[str]) -> Iterable[TFile]:
        return [self.file_type(path) for path in paths]

    def is_folder_allowed_callback(self, value: str) -> bool:
        return not SearchController.is_excluded_or_project_folder(value)

    def is_file_allowed_callback(self, value: str) -> bool:
        return self.file_type.is_model(value)

    def get_find_options(self) -> FindOptions:
        return FindOptions(is_folder_allowed=self.is_folder_allowed_callback,
                           is_file_allowed=self.is_file_allowed_callback,
                           do_stop_recursive=SearchController.is_code_project_folder)

    def files(self) -> Iterable[TFile]:
        find_task = FindPathTask(self.full_path, self.get_find_options())
        return self.get_content(find_task.files())
