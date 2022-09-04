import logging
from typing import Iterable, List, Optional

from icon_manager.config.user import UserConfig
from icon_manager.content.actions.create import (CreateIconAction,
                                                 ReCreateIconAction)
from icon_manager.content.controller.base import ContentController
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.models.matched import MatchedRuleFolder
from icon_manager.crawler.filters import filter_folders
from icon_manager.crawler.options import FilterOptions
from icon_manager.helpers.path import Folder
from icon_manager.helpers.string import prefix_value
from icon_manager.interfaces.builder import CrawlerBuilder
from icon_manager.interfaces.controller import IContentController
from icon_manager.interfaces.path import FolderModel
from icon_manager.library.models import IconSetting
from icon_manager.rules.config import ExcludeRuleConfig

log = logging.getLogger(__name__)


class RulesApplyBuilder(CrawlerBuilder[MatchedRuleFolder]):

    def __init__(self) -> None:
        super().__init__()
        self.settings: Iterable[IconSetting] = []

    def setup(self, **kwargs) -> None:
        self.settings = kwargs.get('settings', [])

    def icon_setting_for(self, model: Folder) -> Optional[IconSetting]:
        for setting in self.settings:
            if not setting.is_config_for(model):
                continue
            return setting
        return None

    def get_matched_folder(self, model: Folder) -> Optional[MatchedRuleFolder]:
        config = self.icon_setting_for(model)
        if config is None:
            return None
        action = prefix_value('Icon', width=7, align='<')
        icon_name = config.icon.name_wo_extension
        icon_name = prefix_value(f'"{icon_name}"', width=25, align='<')
        log.info(f'{action} {icon_name} to "{model.name}"')
        folder = FolderModel(model.path)
        return MatchedRuleFolder(folder, config)

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return True

    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[MatchedRuleFolder]:
        return self.get_matched_folder(folder)


class RulesApplyOptions(FilterOptions):
    def __init__(self) -> None:
        super().__init__(clean_excluded=True, clean_project=True,
                         clean_recursive=True)


class IApplyController(IContentController):

    def crawl_content(self, folders: List[Folder], exclude: ExcludeRuleConfig):
        ...

    def find_matches(self, settings: Iterable[IconSetting]):
        ...

    def apply_matches(self):
        ...

    def re_apply_matches(self, controller: ReApplyController):
        ...

    def delete_content(self):
        ...


class RulesApplyController(ContentController[MatchedRuleFolder], IApplyController):

    def __init__(self, user_config: UserConfig,
                 builder: CrawlerBuilder = RulesApplyBuilder(),
                 options: FilterOptions = RulesApplyOptions()) -> None:
        super().__init__(user_config, builder, options)
        self.existing: List[MatchedRuleFolder] = []
        self.folders: List[MatchedRuleFolder] = []
        self.crawler_folders: List[Folder] = []

    def crawl_content(self, folders: List[Folder], exclude: ExcludeRuleConfig):
        self.options.exclude_rules = exclude
        crawler_folders = filter_folders(folders, self.options)
        self.crawler_folders = crawler_folders

    def find_matches(self, settings: Iterable[IconSetting]):
        self.builder.setup(settings=settings)
        self.folders = self.builder.build_models_async(self.crawler_folders)

    def apply_matches(self):
        action = CreateIconAction(self.folders, self.user_config)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedRuleFolder))

    def re_apply_matches(self, controller: ReApplyController):
        action = ReCreateIconAction(controller, self.user_config)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(MatchedRuleFolder))

    def delete_content(self):
        pass
