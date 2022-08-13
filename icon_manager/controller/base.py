from abc import ABC
from typing import Generic, Iterable, Type, TypeVar

from icon_manager.models.path import FileModel
from icon_manager.tasks.find_folders import FindOptions, FindPathTask

TFile = TypeVar('TFile', bound=FileModel)


class BaseController(ABC, Generic[TFile]):
    def __init__(self, full_path: str, file_type: Type[TFile]) -> None:
        self.full_path = full_path
        self.file_type = file_type

    def get_find_options(self) -> FindOptions:
        return FindOptions(is_folder_allowed=None,
                           is_folder_excluded=FindOptions.default_excluded,
                           is_file_allowed=self.file_type.is_model,
                           do_stop_recursive=FindOptions.default_stop_recursive)

    def files(self) -> Iterable[TFile]:
        find_task = FindPathTask(self.full_path, self.get_find_options())
        return self.get_files(find_task.files())

    def get_files(self, paths: Iterable[str]) -> Iterable[TFile]:
        return [self.file_type(path) for path in paths]
