import os
from abc import abstractmethod
from typing import Dict, Generic, Iterable, List, Set, Type, TypeVar

from icon_manager.controller.search import SearchController
from icon_manager.models.config import IconConfig
from icon_manager.models.path import (DesktopIniFile, FileModel, FolderModel,
                                      IconFile, LocalIconFolder, PathModel)

TPath = TypeVar('TPath', bound=PathModel)
TFile = TypeVar('TFile', bound=FileModel)
TFolder = TypeVar('TFolder', bound=FolderModel)


def create_path(model: PathModel, name: str, path_type: Type[TPath]) -> TPath:
    file_path = os.path.join(model.path, name)
    return path_type(file_path)


def is_code_project(current_path: str, folder_names: Iterable[str]) -> bool:
    if SearchController.is_known_project(current_path):
        return True
    return SearchController.is_project_path(folder_names)


class ContainerModel(FolderModel, Generic[TPath]):
    def __init__(self, full_path: str) -> None:
        super().__init__(full_path)

    def create_file(self, file_name: str, file_type: Type[TFile]) -> TFile:
        return create_path(self, file_name, file_type)

    def create_folder(self, folder_name: str, folder_type: Type[TFolder]) -> TFolder:
        return create_path(self, folder_name, folder_type)

    @abstractmethod
    def build_content(self, root_path: str, folder_names: Iterable[str], file_names: Iterable[str]) -> Iterable[TPath]:
        pass

    def is_path_excluded_already(self, current_path: str, excluded: Iterable[str]) -> bool:
        return any(current_path.startswith(path) for path in excluded)

    def get_content(self) -> Iterable[TPath]:
        do_not_sub_path: Set[str] = set()
        content_items: List[TPath] = []
        for root_path, folder_names, file_names in os.walk(self.path, topdown=True):
            if self.is_path_excluded_already(root_path, do_not_sub_path):
                continue
            if not is_code_project(root_path, folder_names):
                if not self.is_path_excluded_already(root_path, do_not_sub_path):
                    do_not_sub_path.add(root_path)
                continue
            content = self.build_content(root_path, folder_names, file_names)
            content_items.extend(content)
        return content_items


class FolderContainer(ContainerModel[FolderModel]):

    def build_content(self, root_path: str, folder_names: Iterable[str], _: Iterable[str]) -> Iterable[FolderModel]:
        if SearchController.is_folder_excluded(root_path):
            return []
        folders = []
        for folder_name in folder_names:
            if SearchController.is_folder_excluded(folder_name):
                continue
            folder_path = os.path.join(root_path, folder_name)
            folder = FolderModel(folder_path)
            folders.append(folder)
        return folders


class ConfiguredContainer(FolderContainer):
    def __init__(self, folder: FolderModel, config: IconConfig, copy_icon: bool) -> None:
        super().__init__(folder.path)
        self.ini_file = self.create_file(
            DesktopIniFile.file_name, DesktopIniFile)
        self.config = config
        self.copy_icon = copy_icon
        self.errors: Dict[str, Exception] = {}

    def config_icon_path(self) -> str:
        icon_path = self.config.icon_file.path
        if not self.copy_icon:
            return icon_path
        return os.path.relpath(icon_path, self.path)

    def copy_icon_to_local_folder(self) -> IconFile:
        copy_file = self.local_icon_file()
        if copy_file.exists():
            copy_file.remove()
        self.config.icon_file.copy_to(copy_file)
        return copy_file

    def local_icon_folder(self) -> LocalIconFolder:
        folder_name = LocalIconFolder.folder_name
        folder = self.create_folder(folder_name, LocalIconFolder)
        if not folder.exists():
            folder.create()
        return folder

    def local_icon_file(self) -> IconFile:
        local_folder = self.local_icon_folder()
        icon_name = self.config.icon_file.name
        return create_path(local_folder, icon_name, IconFile)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def add_error(self, message: str, exception: Exception):
        self.errors[message] = exception

    def error_messages(self) -> Iterable[str]:
        messages = []
        for message, exception in self.errors.items():
            error_msg = f'ERROR: {self.path}: {message} >> {exception}'
            messages.append(error_msg)
        return messages

    def error_message(self) -> str:
        return '\n'.join(self.error_messages())

    def __str__(self) -> str:
        return f'{self.name} [{self.config}]'

    def __repr__(self) -> str:
        return self.__str__()
