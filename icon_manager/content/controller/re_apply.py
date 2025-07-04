import logging
from typing import Optional, Sequence

from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.models.matched import MatchedIconFolder, MatchedRuleFolder
from icon_manager.interfaces.path import FolderModel
from icon_manager.library.controller import ISettingsHandler
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class ReApplyController:
    def __init__(self, settings: ISettingsHandler, icon_folders: IconFolderController) -> None:
        super().__init__()
        self.settings = settings
        self.icon_folders = icon_folders

    def get_setting_of(self, folder: MatchedIconFolder) -> IconSetting | None:
        for icon in folder.get_icons():
            setting = self.settings.setting_by_icon(icon)
            if setting is None:
                continue
            return setting
        return None

    def get_rule_folders(self) -> Sequence[MatchedRuleFolder]:
        rule_folders = []
        for folder in self.icon_folders.folders_with_icon():
            setting = self.get_setting_of(folder)
            if setting is None:
                continue
            parent = FolderModel(folder.parent_path)
            rule_folder = MatchedRuleFolder(parent, setting)
            rule_folders.append(rule_folder)
        return rule_folders
