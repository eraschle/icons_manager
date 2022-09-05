import logging
from datetime import datetime
from typing import Iterable

from icon_manager.helpers.path import Folder, total_count
from icon_manager.helpers.string import ALIGN_LEFT, ALIGN_RIGHT, fixed_length

log = logging.getLogger(__name__)


def log_time(message: str, start: datetime) -> str:
    diff = (datetime.now() - start).total_seconds()
    diff_value = fixed_length(f'{diff: .2f} sec', width=10, align=ALIGN_RIGHT)
    return f'{message} in {diff_value}'


def execution(message):
    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start = datetime.now()
            result = func(self, *args, **kwargs)
            log_message = fixed_length(message, width=25, align=ALIGN_LEFT)
            config = getattr(self, 'user_config')
            if config is not None:
                name = fixed_length(config.name, width=20, align=ALIGN_LEFT)
                log_message = f'{name}: {log_message}'
            log.info(log_time(log_message, start))
            return result
        return execution_time
    return actual_decorator


def log_files_and_folders(message: str, files: list, folders: list, width: int = 8, suffix: str = '') -> str:
    return log_entry_count(message, len(files), len(folders), width, suffix)


def log_count(message: str, entries: Iterable[Folder], width: int = 8, suffix: str = '') -> str:
    folders, files = total_count(entries)
    return log_entry_count(message, files, folders, width, suffix)


def log_entry_count(prefix: str, files: int, folders: int, width: int = 8, suffix: str = '') -> str:
    file_log = fixed_length(f'{files}', width=width, align=ALIGN_RIGHT)
    file_log = f'{file_log} Files'
    dir_log = fixed_length(f'{folders}', width=width, align=ALIGN_RIGHT)
    dir_log = f'{dir_log} Folders'
    message = f'{prefix} {file_log} / {dir_log}'
    if len(suffix) == 0:
        return message
    return f'{message} {suffix}'
