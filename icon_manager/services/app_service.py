import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Sequence

from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.library.controller import IconLibraryController
from icon_manager.services.base import IConfigService, ServiceProtocol
from icon_manager.services.config_service import ConfigService

log = logging.getLogger(__name__)


def thread_count(services: Sequence[IConfigService]) -> int:
    return len(services) * 10


class IconsAppService(ServiceProtocol):

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.services: List[IConfigService] = []

    def _create_service(self, user_config: UserConfig) -> IConfigService:
        library = IconLibraryController(user_config)
        desktop = DesktopIniController(user_config)
        folders = IconFolderController(user_config)
        files = IconFileController(user_config)
        rules = RulesApplyController(user_config)
        return ConfigService(user_config, settings=library, desktop=desktop,
                             icon_folders=folders, icon_files=files, rules=rules)

    def setup(self):
        for user_config in self.config.user_configs:
            controller = self._create_service(user_config)
            self.services.append(controller)

    def create_settings(self):
        for service in self.services:
            service.create_settings()

    def create_library_configs(self):
        for service in self.services:
            service.create_icon_configs()

    def update_library_configs(self):
        for service in self.services:
            service.update_icon_configs()

    def delete_library_configs(self):
        for service in self.services:
            service.delete_icon_configs()

    def archive_icons_and_configs(self):
        for service in self.services:
            service.archive_library()

    def setup_and_merge_user_service(self):
        for service in self.services:
            service.update_before_and_after(self.config.before_or_after)
            exclude = self.config.create_exclude_rules()
            service.set_exclude_manager(exclude)

    def find_and_apply_matches(self):
        for service in self.services:
            service.find_and_apply()

    def async_find_and_apply_matches(self):
        with ThreadPoolExecutor(thread_name_prefix='find_and_apply_matches',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(srv.find_and_apply)
                                    : srv for srv in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))

    def find_existing_content(self):
        for service in self.services:
            service.find_existing()

    def async_find_existing_content(self):
        with ThreadPoolExecutor(thread_name_prefix='find_existing_content',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(srv.find_existing)
                                    : srv for srv in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))

    def re_apply_matched_icons(self):
        for service in self.services:
            service.re_apply_icons()

    def delete_icon_settings(self):
        for config_service in self.services:
            config_service.delete_setting()

    def async_delete_icon_settings(self):
        with ThreadPoolExecutor(thread_name_prefix='delete_icon_settings',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(srv.delete_setting)
                                    : srv for srv in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))
