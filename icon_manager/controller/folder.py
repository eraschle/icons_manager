from icon_manager.controller.base import BaseController
from icon_manager.models.path import FileModel, FolderModel


class FolderController(BaseController[FileModel, FolderModel]):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path, folder_type=FolderModel)
