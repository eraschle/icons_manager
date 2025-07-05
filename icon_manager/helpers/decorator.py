import logging
from datetime import datetime
from typing import Sequence

from icon_manager.helpers.logs import log_begin, log_end
from icon_manager.helpers.string import ALIGN_RIGHT, THOUSAND, list_value
from icon_manager.interfaces.actions import Action

log = logging.getLogger(__name__)


def execution(message, start_message=None):
    """
    Decorator factory that logs the start and end of a method's execution, including its duration.
    
    If a `start_message` is provided, it is logged before the method runs. After execution, the specified `message` is logged along with the elapsed time. The decorator retrieves a `user_config` attribute from the instance for contextual logging.
    """
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
    """
    Format a log message that includes a list of files.
    
    Parameters:
    	files (Sequence): The collection of files to include in the log message.
    	message (str): The base message to prepend to the file list.
    
    Returns:
    	str: The formatted log message with the file list.
    """
    files_log = list_value(files, width=width, align=align)
    return f'{message} Files: {files_log}'


def log_folders(folders: Sequence, message, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    """
    Format a log message that includes a list of folders.
    
    Parameters:
        folders (Sequence): The folders to include in the log message.
        message (str): The base message to prepend to the folder list.
    
    Returns:
        str: The formatted log message with folder information.
    """
    folders_log = list_value(folders, width=width, align=align)
    return f'{message} Folders: {folders_log}'


def execution_action(message, start_message=None):
    """
    A decorator factory that logs the start and end of a method execution, including execution time and details about files or folders in the returned Action.
    
    If the decorated method returns an Action instance with non-empty `files` or `folders` attributes, the log message is augmented with formatted information about these items.
    """
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
