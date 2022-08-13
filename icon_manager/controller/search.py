from typing import Iterable, Union
from icon_manager.utils.path import get_path_names


def path_contains_names(values: Iterable[str], full_path: Union[str, Iterable[str]]) -> bool:
    if not isinstance(full_path, str):
        return any(path_contains_names(values, val) for val in full_path)
    path_names = get_path_names(full_path)
    return any(name in values for name in path_names)


def are_values_in_path(values: Iterable[str], full_path: Union[str, Iterable[str]]) -> bool:
    if not isinstance(full_path, str):
        return any(are_values_in_path(values, val) for val in full_path)
    return any(value in full_path for value in values)


def is_value_in_values(values: Iterable[str], value: Union[str, Iterable[str]]) -> bool:
    if not isinstance(value, str):
        return any(is_value_in_values(values, val) for val in value)
    return value in values


class SearchController:

    excluded_folder_names: Iterable[str] = []
    project_folder_names: Iterable[str] = []

    @classmethod
    def is_folder_excluded(cls, value: Union[str, Iterable[str]]) -> bool:
        return is_value_in_values(cls.excluded_folder_names, value)

    @ classmethod
    def is_code_project_folder(cls, folder: Union[str, Iterable[str]]) -> bool:
        return is_value_in_values(cls.project_folder_names, folder)

    @classmethod
    def is_excluded_or_project_folder(cls, value: Union[str, Iterable[str]]) -> bool:
        return cls.is_folder_excluded(value) or cls.is_code_project_folder(value)

    @ classmethod
    def is_project_path(cls, full_path: str) -> bool:
        return path_contains_names(cls.project_folder_names, full_path)

    @classmethod
    def is_path_excluded(cls, full_path: str) -> bool:
        return path_contains_names(cls.excluded_folder_names, full_path)
