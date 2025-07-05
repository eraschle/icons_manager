import logging
from typing import Iterable, List, Optional, Sequence

from icon_manager.config.user import UserConfig
from icon_manager.content.actions.create import CreateIconAction, ReCreateIconAction
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.models.matched import MatchedRuleFolder
from icon_manager.crawler.filters import filter_folders
from icon_manager.crawler.options import FilterOptions
from icon_manager.helpers.decorator import execution, execution_action
from icon_manager.helpers.string import ALIGN_LEFT, prefix_value
from icon_manager.interfaces.actions import Action
from icon_manager.interfaces.builder import FolderCrawlerBuilder
from icon_manager.interfaces.path import Folder, FolderModel
from icon_manager.library.models import IconSetting
from icon_manager.rules.manager import ExcludeManager

log = logging.getLogger(__name__)


class RulesApplyBuilder(FolderCrawlerBuilder[MatchedRuleFolder]):
    def __init__(self) -> None:
        super().__init__()
        self.settings: Sequence[IconSetting] = []

    def setup(self, **kwargs) -> None:
        self.settings = kwargs.get("settings", [])

    def icon_setting_for(self, model: Folder) -> IconSetting | None:
        for setting in self.settings:
            if not setting.is_config_for(model):
                continue
            return setting
        return None

    def get_matched_folder(self, model: Folder) -> MatchedRuleFolder | None:
        config = self.icon_setting_for(model)
        if config is None:
            return None
        action = prefix_value("Icon", width=7, align=ALIGN_LEFT)
        icon_name = config.icon.name_wo_extension
        icon_name = prefix_value(f'"{icon_name}"', width=25, align=ALIGN_LEFT)
        log.debug(f'{action} {icon_name} to "{model.name}"')
        folder = FolderModel(model.path)
        return MatchedRuleFolder(folder, config)

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return True

    def build_folder_model(self, folder: Folder, **kwargs) -> MatchedRuleFolder | None:
        return self.get_matched_folder(folder)


class RulesApplyOptions(FilterOptions):
    def __init__(self, exclude: ExcludeManager) -> None:
        super().__init__(exclude, clean_excluded=True, clean_project=True, clean_recursive=True)

    def no_filter_options(self) -> bool:
        return (
            not self.clean_excluded and not self.clean_project and not self.clean_recursive and self.exclude.is_empty()
        )


class RulesApplyController:
    def __init__(
        self,
        user_config: UserConfig,
        builder: FolderCrawlerBuilder = RulesApplyBuilder(),
    ) -> None:
        self.user_config = user_config
        self.builder = builder
        self.folders: list[MatchedRuleFolder] = []

    @execution(message="Crawle and filter result")
    def crawle_and_build_result(self, folders: list[Folder], exclude: ExcludeManager) -> list[Folder]:
        folders = filter_folders(folders, RulesApplyOptions(exclude))
        # folders = clean_excluded_folders(folders)
        return folders

    @execution(message="Searched for matches", start_message="Searching for matches")
    def search_and_find_matches(self, folders: list[Folder], settings: Iterable[IconSetting]):
        self.builder.setup(settings=settings)
        self.folders = self.builder.build_models(folders)

    @ execution_action(message='Created matched icons', start_message='Creating matched icons')
    def creating_found_matches(self, exclude: ExcludeManager) -> Action:
        action = CreateIconAction(self.folders, self.user_config)
        action.async_execute()
        if not action.any_executed():
            return action
        return action

    def re_apply_matches(self, controller: ReApplyController):
        action = ReCreateIconAction(controller, self.user_config)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedRuleFolder))

    def delete_content(self):
        pass
