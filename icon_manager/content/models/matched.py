import logging
import os
from typing import Sequence

from icon_manager.content.models.desktop import DesktopIniFile
from icon_manager.helpers.path import get_files
from icon_manager.library.models import IconFile, IconSetting, LibraryIconFile
from icon_manager.interfaces.path import FolderModel

log = logging.getLogger(__name__)


class MatchedIconFile(IconFile):
    pass


class MatchedIconFolder(FolderModel):

    folder_name: str = '__icon__'

    @ classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.folder_name)

    def __init__(self, path: str) -> None:
        super().__init__(path)

    def create_icon(self, library_icon: LibraryIconFile) -> MatchedIconFile:
        icon_path = self.child_path(library_icon.name)
        return MatchedIconFile(icon_path)

    def get_icons(self) -> Sequence[IconFile]:
        icon_paths = get_files(self.path, MatchedIconFile.extension())
        return [IconFile(path) for path in icon_paths]


class MatchedRuleFolder(FolderModel):

    def __init__(self, entry: FolderModel, setting: IconSetting) -> None:
        super().__init__(entry.path)
        self.setting = setting

    @ property
    def library_icon(self) -> LibraryIconFile:
        return self.setting.icon

    @ property
    def desktop_ini(self) -> DesktopIniFile:
        file_path = self.child_path(DesktopIniFile.file_name)
        return DesktopIniFile(file_path)

    @ property
    def icon_folder(self) -> MatchedIconFolder:
        path = self.child_path(MatchedIconFolder.folder_name)
        return MatchedIconFolder(path)

    @ property
    def local_icon(self) -> MatchedIconFile:
        return self.icon_folder.create_icon(self.library_icon)

    def icon_path_for_desktop_ini(self) -> str:
        if self.local_icon.exists():
            local_path = self.local_icon.path
            return os.path.relpath(local_path, self.path)
        return self.library_icon.path

    def __str__(self) -> str:
        return f'{self.name} [{self.setting}]'

    def __repr__(self) -> str:
        return self.__str__()
