import os
from typing import Collection, Iterable, List, Optional

from icon_manager.controller.base import BaseController
from icon_manager.models.path import DesktopIniFile, LocalIconFolder, PathModel
from icon_manager.tasks.find_folders import FindOptions, FindPathTask


class FolderConfigController(BaseController[DesktopIniFile]):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path, DesktopIniFile)

    def get_find_options(self) -> FindOptions:
        options = super().get_find_options()
        options.stop_recursive = None
        return options

    def get_icon_folder(self, path: str) -> Optional[LocalIconFolder]:
        parent_dir = os.path.dirname(path)
        folder_path = os.path.join(parent_dir, LocalIconFolder.folder_name)
        folder = LocalIconFolder(folder_path)
        if not folder.exists():
            return None
        return folder

    def get_file(self, path: str) -> DesktopIniFile:
        folder = self.get_icon_folder(path)
        return self.file_type(path, folder)

    def get_files(self, paths: Iterable[str]) -> Iterable[DesktopIniFile]:
        return [self.get_file(path) for path in paths]

    def remove_existing_configs(self) -> Collection[PathModel]:
        removed: List[PathModel] = []
        removed.extend(self.remove_existing_files())
        removed.extend(self.remove_existing_folders())
        return removed

    def remove_existing_files(self) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for file in self.files():
            folder = file.icon_folder
            if folder is not None:
                # folder.remove()
                removed.append(folder)
            # file.remove()
            removed.append(file)
        return removed

    def get_folders_options(self) -> FindOptions:
        options = self.get_find_options()
        options.is_folder_allowed = LocalIconFolder.is_model
        options.stop_recursive = None
        return options

    def folders(self) -> Iterable[LocalIconFolder]:
        task = FindPathTask(self.full_path, self.get_folders_options())
        return [LocalIconFolder(folder) for folder in task.folders()]

    def remove_existing_folders(self) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for folder in self.folders():
            # folder.remove()
            removed.append(folder)
        return removed
