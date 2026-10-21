import logging
import os
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from icon_manager.config.app import AppConfig
from icon_manager.config.user import UserConfig
from icon_manager.content.controller.desktop import DesktopIniController
from icon_manager.content.controller.icon_file import IconFileController
from icon_manager.content.controller.icon_folder import IconFolderController
from icon_manager.content.controller.rules_apply import RulesApplyController
from icon_manager.library.controller import IconLibraryController
from icon_manager.services.config_service import ConfigService

log = logging.getLogger(__name__)


def thread_count(services: Sequence[ConfigService]) -> int:
    return len(services) + (os.cpu_count() or 5) - 2


class IconsAppService:
    """Runs one :class:`ConfigService` per user configuration.

    Every operation is the same fan-out over those services, which is why
    they all go through :meth:`_for_each`: the only difference between them
    is whether the user configurations may be processed concurrently.
    Operations that walk the search folders may, because they touch disjoint
    folder trees; operations on the icon library may not, because several
    user configurations can point at the same library.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.services: list[ConfigService] = []

    def _create_service(self, user_config: UserConfig) -> ConfigService:
        return ConfigService(
            user_config,
            settings=IconLibraryController(user_config),
            desktop=DesktopIniController(user_config),
            icon_folders=IconFolderController(user_config),
            icon_files=IconFileController(user_config),
            rules=RulesApplyController(user_config),
        )

    def setup(self) -> None:
        for user_config in self.config.user_configs:
            self.services.append(self._create_service(user_config))

    def _for_each(self, operation: str, concurrent: bool = False) -> None:
        """Call ``operation`` on every service, logging but not re-raising.

        One failing user configuration must not abort the others, so the
        exception is logged against the configuration that caused it.
        """
        if not concurrent or len(self.services) < 2:
            for service in self.services:
                try:
                    getattr(service, operation)()
                except Exception as exc:
                    log.error("%r Exception: %s", service.user_config, exc)
            return
        with ThreadPoolExecutor(thread_name_prefix=operation, max_workers=thread_count(self.services)) as executor:
            tasks = {executor.submit(getattr(service, operation)): service for service in self.services}
            for future in as_completed(tasks):
                service = tasks[future]
                try:
                    future.result()
                except Exception as exc:
                    log.error("%r Exception: %s", service.user_config, exc)

    # --- icon library -----------------------------------------------------

    def create_settings(self) -> None:
        self._for_each("create_settings")

    def create_library_configs(self) -> None:
        self._for_each("create_icon_configs")

    def update_library_configs(self) -> None:
        self._for_each("update_icon_configs")

    def delete_library_configs(self) -> None:
        self._for_each("delete_icon_configs")

    def archive_icons_and_configs(self) -> None:
        self._for_each("archive_library")

    # --- search folders ---------------------------------------------------

    def setup_and_merge_user_service(self) -> None:
        for service in self.services:
            service.update_before_and_after(self.config.before_or_after)
            service.set_exclude_manager(self.config.create_exclude_rules())

    def find_and_apply_matches(self) -> None:
        self._for_each("find_and_apply_matches", concurrent=True)

    def find_existing_content(self) -> None:
        self._for_each("find_existing_content", concurrent=True)

    def re_apply_matched_icons(self) -> None:
        self._for_each("re_apply_icons")

    def delete_icon_settings(self) -> None:
        self._for_each("delete_content", concurrent=True)
