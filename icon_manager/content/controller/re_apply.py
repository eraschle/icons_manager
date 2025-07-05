import logging
from typing import Optional, Sequence

from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.models.matched import (MatchedIconFolder,
                                                 MatchedRuleFolder)
from icon_manager.interfaces.path import FolderModel
from icon_manager.library.controller import ISettingsHandler
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class ReApplyController:

    def __init__(self, settings: ISettingsHandler, icon_folders: IconFolderController) -> None:
        super().__init__()
        self.settings = settings
        self.icon_folders = icon_folders

    def get_setting_of(self, folder: MatchedIconFolder) -> Optional[IconSetting]:
        """
        Return the first icon setting found for any icon in the given folder.
        
        Parameters:
            folder (MatchedIconFolder): The folder whose icons are checked for associated settings.
        
        Returns:
            Optional[IconSetting]: The first found icon setting, or None if no setting exists for any icon in the folder.
        """
        for icon in folder.get_icons():
            setting = self.settings.setting_by_icon(icon)
            if setting is None:
                continue
            return setting
        return None

    def get_rule_folders(self) -> Sequence[MatchedRuleFolder]:
        """
        Return a sequence of matched rule folders, each representing a parent folder with an associated icon setting.
        
        Returns:
            Sequence[MatchedRuleFolder]: A list of rule folders where each folder's parent path is paired with its icon setting.
        """
        rule_folders = []
        for folder in self.icon_folders.folders_with_icon():
            setting = self.get_setting_of(folder)
            if setting is None:
                continue
            parent = FolderModel(folder.parent_path)
            rule_folder = MatchedRuleFolder(parent, setting)
            rule_folders.append(rule_folder)
        return rule_folders
