from typing import Collection, Iterable, List, Optional

from icon_manager.controller.base import FileBaseController
from icon_manager.models.path import DesktopIniFile, LocalIconFolder, PathModel
from icon_manager.tasks.find_folders import File, FindOptions, Folder


class LocalConfigController(FileBaseController[DesktopIniFile]):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path, DesktopIniFile)
        self.icon_folders: List[LocalIconFolder] = []

    def get_find_options(self) -> FindOptions:
        options = super().get_find_options()
        options.add_folder_allowed(LocalIconFolder.is_model)
        options.clear_stop_recursive()
        return options

    def get_icon_folder(self, folders: Iterable[Folder]) -> Optional[LocalIconFolder]:
        for folder in folders:
            if not LocalIconFolder.is_model(folder.full_path):
                continue
            return LocalIconFolder(folder.full_path)
        return None

    def on_found_folders_and_files(self, folders: Iterable[Folder], files: Iterable[File]) -> None:
        super().on_found_folders_and_files(folders, files)
        self.icon_folders.extend(self.create_folders(folders))

    def create_folders(self, folders: Iterable[Folder]) -> Iterable[LocalIconFolder]:
        return [LocalIconFolder(folder.full_path) for folder in folders]

    def get_file(self, folders: Iterable[Folder], file: File) -> DesktopIniFile:
        folder = self.get_icon_folder(folders)
        return self.file_type(file.full_path, folder)

    def create_files(self, folders: Iterable[Folder], files: Iterable[File]) -> Iterable[DesktopIniFile]:
        return [self.get_file(folders, file) for file in files]

    def delete_existing_configs(self) -> Collection[PathModel]:
        removed: List[PathModel] = []
        removed.extend(self.delete_existing_files())
        removed.extend(self.delete_existing_folders())
        return removed

    def delete_existing_files(self) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for file in self.get_files():
            folder = file.icon_folder
            if folder is not None:
                folder.remove()
                removed.append(folder)
            file.remove()
            removed.append(file)
        return removed

    def delete_existing_folders(self) -> Iterable[PathModel]:
        removed: List[PathModel] = []
        for folder in self.icon_folders:
            if not folder.exists():
                continue
            folder.remove()
            removed.append(folder)
        return removed
