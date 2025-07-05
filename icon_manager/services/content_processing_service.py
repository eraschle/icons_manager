import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from icon_manager.services.base import IConfigService

log = logging.getLogger(__name__)


def _thread_count(services: List[IConfigService]) -> int:
    """Calculate optimal thread count for async operations."""
    import os
    return len(services) + (os.cpu_count() or 5) - 2


class ContentProcessingService:
    """Focused service for processing folder and file icon content.
    
    Responsibilities:
    - Find and apply icon matches
    - Re-apply existing matched icons
    - Find existing content
    - Delete icon settings
    """
    
    def __init__(self, services: List[IConfigService]) -> None:
        self.services = services
    
    def find_and_apply_matches(self) -> None:
        """Find and apply icon matches synchronously."""
        for service in self.services:
            service.find_and_apply()
    
    def async_find_and_apply_matches(self) -> None:
        """Find and apply icon matches asynchronously for better performance."""
        with ThreadPoolExecutor(
            thread_name_prefix='find_and_apply_matches',
            max_workers=_thread_count(self.services)
        ) as executor:
            tasks = {executor.submit(service.find_and_apply): service for service in self.services}
            for future in as_completed(tasks):
                service = tasks[future]
                try:
                    future.result()
                except Exception as exc:
                    log.error("Service %r Exception: %s", service.user_config, exc)
    
    def find_existing_content(self) -> None:
        """Find existing content synchronously."""
        for service in self.services:
            service.find_existing()
    
    def async_find_existing_content(self) -> None:
        """Find existing content asynchronously for better performance."""
        with ThreadPoolExecutor(
            thread_name_prefix='find_existing_content',
            max_workers=_thread_count(self.services)
        ) as executor:
            tasks = {executor.submit(service.find_existing): service for service in self.services}
            for future in as_completed(tasks):
                service = tasks[future]
                try:
                    future.result()
                except Exception as exc:
                    log.error("Service %r Exception: %s", service.user_config, exc)
    
    def re_apply_matched_icons(self) -> None:
        """Re-apply previously matched icons."""
        for service in self.services:
            service.re_apply_icons()
    
    def delete_icon_settings(self) -> None:
        """Delete icon settings synchronously."""
        for service in self.services:
            service.delete_setting()
    
    def async_delete_icon_settings(self) -> None:
        """Delete icon settings asynchronously for better performance."""
        with ThreadPoolExecutor(
            thread_name_prefix='delete_icon_settings',
            max_workers=_thread_count(self.services)
        ) as executor:
            tasks = {executor.submit(service.delete_setting): service for service in self.services}
            for future in as_completed(tasks):
                service = tasks[future]
                try:
                    future.result()
                except Exception as exc:
                    log.error("Service %r Exception: %s", service.user_config, exc)