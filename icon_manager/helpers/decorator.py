import logging
from datetime import datetime
from typing import Sequence

from icon_manager.helpers.logs import log_begin, log_end
from icon_manager.helpers.string import ALIGN_RIGHT, THOUSAND, list_value
from icon_manager.interfaces.actions import Action

log = logging.getLogger(__name__)


def execution(message, start_message=None):
    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            config = getattr(self, 'user_config', None)
            if start_message is not None:
                log.info(log_begin(config, start_message, start_time))
            result = func(self, *args, **kwargs)
            log.info(log_end(config, message, start_time))
            return result
        return execution_time
    return actual_decorator


def log_files(files: Sequence, message, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    files_log = list_value(files, width=width, align=align)
    return f'{message} Files: {files_log}'


def log_folders(folders: Sequence, message, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    folders_log = list_value(folders, width=width, align=align)
    return f'{message} Folders: {folders_log}'


def execution_action(message, start_message=None):
    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            config = getattr(self, 'user_config', None)
            if start_message is not None:
                log.info(log_begin(config, start_message, start_time))
            result = func(self, *args, **kwargs)
            log_msg = message
            if isinstance(result, Action):
                if len(result.files) > 0:
                    log_msg = log_files(result.files, log_msg)
                if len(result.folders) > 0:
                    log_msg = log_folders(result.folders, log_msg)
            log.info(log_end(config, log_msg, start_time))
            return result
        return execution_time
    return actual_decorator
