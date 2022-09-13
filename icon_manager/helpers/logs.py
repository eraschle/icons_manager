import logging
from datetime import datetime
from typing import Iterable, Optional

from icon_manager.config.user import UserConfig
from icon_manager.helpers.path import total_count
from icon_manager.helpers.string import ALIGN_LEFT, ALIGN_RIGHT, fixed_length
from icon_manager.interfaces.path import Folder

log = logging.getLogger(__name__)


def get_time_log(message: str, width: int = 12) -> str:
    return fixed_length(message, width=width, align=ALIGN_RIGHT)


def get_time_msg(start: datetime) -> str:
    diff = (datetime.now() - start).total_seconds()
    return get_time_log(f'{diff: .2f} sec')


def log_time(message: str, start: datetime) -> str:
    return f'{message} in {get_time_msg(start)}'


def _config_message(config: Optional[UserConfig], message: str,
                    width_config: int = 20, width_message: int = 60):
    name = fixed_length('', width=width_config, align=ALIGN_LEFT)
    if config is not None:
        name = fixed_length(config.name, width=width_config, align=ALIGN_LEFT)
    log_message = fixed_length(message, width=width_message, align=ALIGN_LEFT)
    return f'{name}: {log_message}'


def log_begin(config: Optional[UserConfig], message: str, start_time: datetime):
    message = _config_message(config, message)
    start_value = start_time.strftime("%H:%M:%S")
    return f'{message} at {get_time_log(start_value)}'


def log_end(config: Optional[UserConfig], message: str, start_time: datetime):
    message = _config_message(config, message)
    return log_time(message, start_time)


def log_files_and_folders(message: str, files: list, folders: list, width: int = 8, suffix: str = '') -> str:
    return log_entries_count(message, len(files), len(folders), width, suffix)


def log_list_count(message: str, entries: Iterable[Folder], width: int = 8, suffix: str = '') -> str:
    folders, files = total_count(entries)
    return log_entries_count(message, files, folders, width, suffix)


def log_ending(result, message: str, start_time: datetime):
    time_msg = f' in {get_time_msg(start_time)}'
    if isinstance(result, dict):
        return log_apply_icons(message, result, suffix=time_msg)
    return log_list_count(message, result, suffix=time_msg)


def log_entries_count(prefix: str, files: int, folders: int, width: int = 8, suffix: str = '') -> str:
    file_log = fixed_length(f'{files}', width=width, align=ALIGN_RIGHT)
    file_log = f'{file_log} Files'
    dir_log = fixed_length(f'{folders}', width=width, align=ALIGN_RIGHT)
    dir_log = f'{dir_log} Folders'
    message = f'{prefix} {file_log} / {dir_log}'
    if len(suffix) == 0:
        return message
    return f'{message} {suffix}'


def log_apply_icons(prefix: str, file_map: dict, width: int = 8, suffix: str = '') -> str:
    file_messages = []
    for ext, files in file_map.items():
        count = str(len(files))
        file_msg = f'{ext} {fixed_length(count, width=width, align=ALIGN_RIGHT)}'
        file_messages.append(file_msg)
    message = f'{prefix} {" / ".join(file_messages)}'
    if len(suffix) == 0:
        return message
    return f'{message} {suffix}'
