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
    """
    Calculate the number of threads to allocate for concurrent execution based on the number of services.
    
    Parameters:
        services (Sequence[IConfigService]): The collection of icon configuration services.
    
    Returns:
        int: The total number of threads, computed as ten times the number of services.
    """
    return len(services) * 10


class IconsAppService(ServiceProtocol):

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize the IconsAppService with the provided application configuration.
        
        Parameters:
            config (AppConfig): The application configuration used to set up icon services.
        """
        self.config = config
        self.services: List[IConfigService] = []

    def _create_service(self, user_config: UserConfig) -> IConfigService:
        """
        Create and return a configuration service for the specified user configuration.
        
        Initializes all necessary controllers for icon management and passes them to the ConfigService instance.
        """
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
        """
        Create icon settings for all configured user services.
        """
        for service in self.services:
            service.create_icon_settings()

    def create_library_configs(self):
        """
        Create icon library configurations for all user services.
        """
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
        """
        Finds and applies icon matches for each user configuration service.
        """
        for service in self.services:
            service.find_and_apply()

    def async_find_and_apply_matches(self):
        """
        Concurrently executes the `find_and_apply` operation across all icon configuration services.
        
        Each service's `find_and_apply` method is run in a separate thread. Exceptions raised during execution are caught and printed along with the associated user configuration.
        """
        with ThreadPoolExecutor(thread_name_prefix='find_and_apply_matches',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(service.find_and_apply): service for service in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))

    def find_existing_content(self):
        """
        Finds existing icon content for all configured services by invoking their `find_existing` method.
        """
        for service in self.services:
            service.find_existing()

    def async_find_existing_content(self):
        """
        Concurrently executes the `find_existing` method on all icon configuration services to locate existing icon content.
        
        Exceptions raised during execution are caught and printed along with the associated user configuration.
        """
        with ThreadPoolExecutor(thread_name_prefix='find_existing_content',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(service.find_existing): service for service in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))

    def re_apply_matched_icons(self):
        """
        Re-applies matched icons for all configured services.
        """
        for service in self.services:
            service.re_apply_icons()

    def delete_icon_settings(self):
        """
        Deletes icon settings for all user configuration services managed by this instance.
        """
        for config_service in self.services:
            config_service.delete_setting()

    def async_delete_icon_settings(self):
        """
        Deletes icon settings concurrently across all services using a thread pool.
        
        Exceptions raised during deletion are caught and printed along with the associated user configuration.
        """
        with ThreadPoolExecutor(thread_name_prefix='delete_icon_settings',
                                max_workers=thread_count(self.services)) as executor:
            task = {executor.submit(service.delete_setting): service for service in self.services}
            for future in as_completed(task):
                user_service = task[future]
                try:
                    future.result()
                except Exception as exc:
                    print('%r Exception: %s' % (user_service.user_config, exc))
