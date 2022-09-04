import logging
from datetime import datetime
from typing import Iterable

from icon_manager.helpers.path import Folder, total_count
from icon_manager.helpers.string import ALIGN_RIGHT, fixed_length

log = logging.getLogger(__name__)


def log_time(message: str, start: datetime) -> str:
    diff = (datetime.now() - start).total_seconds()
    duration = fixed_length(f'{diff:.2f} sec', width=8, align=ALIGN_RIGHT)
    return f'{message} in {duration}'


def execution(*args, **kwargs):

    message = kwargs.get('message', '')

    def inner(func):

        def execution_time(*args, **kwargs):

            start = datetime.now()
            # log.info(f'Started {func.__name__}')
            result = func(*args, **kwargs)
            log.info(log_time(message, start))
            return result
        return execution_time
    return inner


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
