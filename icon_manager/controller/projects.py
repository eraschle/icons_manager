import os
from datetime import datetime
from typing import Iterable, List, Set

from icon_manager.controller.search import SearchController
from icon_manager.models.path import FolderModel


class ProjectsController:

    def __init__(self, folders: Iterable[FolderModel]) -> None:
        self.folders = folders
        self.projects: Set[str] = set()
        self.total_paths: List[str] = []

    def is_project_folder(self, folder_names: Iterable[str]) -> bool:
        return SearchController.is_code_project_folder(folder_names)

    def is_known_code_project(self, path: str) -> bool:
        return any(path.startswith(project) for project in self.projects)

    def is_excluded(self, path: str) -> bool:
        return SearchController.is_folder_excluded(path)

    def is_folder(self, path: str, name: str) -> bool:
        if self.is_excluded(name):
            return False
        return os.path.isdir(os.path.join(path, name))

    def get_folders(self, path: str):
        return [name for name in os.listdir(path) if self.is_folder(path, name)]

    def collect_projects_in_path(self, current_path: str):
        folder_names = self.get_folders(current_path)
        if SearchController.is_code_project_folder(folder_names):
            self.projects.add(current_path)
            return
        for name in folder_names:
            full_path = os.path.join(current_path, name)
            self.total_paths.append(current_path)
            self.collect_projects_in_path(full_path)

    # def collect_projects_in(self, folder: FolderModel):
    #     for path, folders, files in os.walk(folder.path, topdown=True):
    #         self.total_paths.append(path)
    #         if self.is_excluded(path):
    #             continue
    #         if self.is_known_code_project(path):
    #             # print(f'KNOWN PROJECT >> {path}')
    #             continue
    #         if not self.has_project_names(path, folders, files):
    #             continue
    #         # print(f'PROJECT >> {path}')
    #         self.projects.add(path)

    def collect_projects(self):
        start = datetime.now()
        for folder in self.folders:
            self.collect_projects_in_path(folder.path)
        end = datetime.now()
        diff = end-start
        message = f'Projects "{len(self.projects)}"/"{len(self.total_paths)}" [{diff.total_seconds()}]'
        print(message)
