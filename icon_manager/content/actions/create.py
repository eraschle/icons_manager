import logging
from collections.abc import Iterable

from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniCreator
from icon_manager.content.controller.re_apply import ReApplyController
from icon_manager.content.models.matched import MatchedRuleFolder
from icon_manager.interfaces.actions import Action

log = logging.getLogger(__name__)


class CreateIconAction(Action[MatchedRuleFolder]):
    def __init__(
        self,
        entries: Iterable[MatchedRuleFolder],
        user_config: UserConfig,
        action_log: str = "Added Icons to Folders",
        controller: DesktopIniCreator = DesktopIniCreator(),
    ) -> None:
        super().__init__(entries, action_log)
        self.user_config = user_config
        self.controller = controller

    def can_execute(self, entry: MatchedRuleFolder) -> bool:
        if not entry.desktop_ini.exists():
            return True
        can_write = self.controller.can_write(entry.desktop_ini)
        if not can_write:
            log.warning(f'Can not write desktop.ini in "{entry.path}"')
        return can_write

    def execute_action(self, entry: MatchedRuleFolder) -> None:
        search_folder = self.user_config.search_folder_by(entry)
        copy_icon = search_folder.copy_icon
        if copy_icon is None:
            copy_icon = self.user_config.copy_icon
        if entry.setting.copy_icon is not None:
            copy_icon = entry.setting.copy_icon
        self.controller.write(entry, copy_icon)

    def get_log_message(self, model: type) -> str:
        name = self._log_prefix(model)
        action = self._log_action()
        folders = self._log_folders()
        return f'{name}: {action} "{folders}" Folders'


class ReCreateIconAction(CreateIconAction):
    def __init__(
        self,
        re_apply: ReApplyController,
        user_config: UserConfig,
        controller: DesktopIniCreator = DesktopIniCreator(),
    ) -> None:
        super().__init__(
            re_apply.get_rule_folders(),
            user_config,
            action_log="Re added Icons to folder",
            controller=controller,
        )
