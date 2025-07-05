import logging
from typing import Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.base import ContentController
from icon_manager.content.models.matched import MatchedIconFolder
from icon_manager.crawler.filters import folders_by_name
from icon_manager.helpers.decorator import execution, execution_action
from icon_manager.interfaces.path import Folder
from icon_manager.interfaces.actions import Action, DeleteAction
from icon_manager.interfaces.builder import FolderCrawlerBuilder
from icon_manager.library.models import IconSetting

log = logging.getLogger(__name__)


class IconFolderBuilder(FolderCrawlerBuilder[MatchedIconFolder]):

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return folder.name == MatchedIconFolder.folder_name

    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[MatchedIconFolder]:
        return MatchedIconFolder(folder.path)


class IconFolderController(ContentController[MatchedIconFolder]):

    def __init__(self, user_config: UserConfig,
                 builder: FolderCrawlerBuilder = IconFolderBuilder()) -> None:
        super().__init__(user_config, builder)
        self.folders: List[MatchedIconFolder] = []

    @execution(message='Crawle & build __icon__ folder')
    def crawle_and_build_result(self, folders: List[Folder], _: Sequence[IconSetting]):
        """
        Filters the provided folders for those named '__icon__' and builds models for them.
        
        The resulting list of matched icon folder models is stored in the controller's `self.folders` attribute.
        """
        folders = folders_by_name(folders, [MatchedIconFolder.folder_name])
        self.folders = self.builder.build_models(folders)

    @execution_action(message='Deleted existing __icon__ folder')
    def delete_content(self) -> Action:
        """
        Deletes all matched icon folders and returns the corresponding action.
        
        Returns:
            Action: The action object representing the deletion operation, regardless of whether any folders were actually deleted.
        """
        action = DeleteAction(self.user_config, self.folders)
        action.execute()
        if not action.any_executed():
            return action
        return action

    def folders_with_icon(self) -> Iterable[MatchedIconFolder]:
        """
        Return an iterable of matched icon folders that contain at least one icon.
        
        Returns:
            Iterable[MatchedIconFolder]: Folders from the current list that have one or more icons.
        """
        return [folder for folder in self.folders if len(folder.get_icons()) > 0]
