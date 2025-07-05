import logging
from datetime import datetime
from typing import Optional

from icon_manager.config.user import UserConfig
from icon_manager.helpers.string import ALIGN_LEFT, ALIGN_RIGHT, fixed_length

log = logging.getLogger(__name__)


def get_time_log(message: str, width: int = 12) -> str:
    """
    Format a message as a right-aligned string with a fixed width.
    
    Parameters:
        message (str): The message to format.
        width (int): The total width of the formatted string. Defaults to 12.
    
    Returns:
        str: The right-aligned, fixed-width message.
    """
    return fixed_length(message, width=width, align=ALIGN_RIGHT)


def get_time_msg(start: datetime) -> str:
    """
    Return the elapsed time in seconds since the given start time, formatted as a right-aligned string with two decimal places and a "sec" suffix.
    
    Parameters:
        start (datetime): The starting time to measure elapsed duration from.
    
    Returns:
        str: The formatted elapsed time string.
    """
    diff = (datetime.now() - start).total_seconds()
    return get_time_log(f'{diff: .2f} sec')


def log_time(message: str, start: datetime) -> str:
    """
    Return a formatted string combining a message with the elapsed time since the given start datetime.
    
    Returns:
        str: The message followed by the elapsed time in seconds, formatted as "`message` in `X.XX sec`".
    """
    return f'{message} in {get_time_msg(start)}'


def _config_message(config: Optional[UserConfig], message: str,
                    width_config: int = 20, width_message: int = 60):
    name = fixed_length('', width=width_config, align=ALIGN_LEFT)
    if config is not None:
        name = fixed_length(config.name, width=width_config, align=ALIGN_LEFT)
    log_message = fixed_length(message, width=width_message, align=ALIGN_LEFT)
    return f'{name}: {log_message}'


def log_begin(config: Optional[UserConfig], message: str, start_time: datetime):
    """
    Return a formatted string indicating the start of an operation, including the configuration name (if provided), a message, and the start time.
    
    The output combines the configuration name (if any), the message, and the start time formatted as "HH:MM:SS" and right-aligned.
    """
    message = _config_message(config, message)
    start_value = start_time.strftime("%H:%M:%S")
    return f'{message} at {get_time_log(start_value)}'


def log_end(config: Optional[UserConfig], message: str, start_time: datetime):
    """
    Return a formatted string combining a configuration name, message, and the elapsed time since the given start time.
    
    The output includes the configuration name (if provided), the message, and the elapsed time in seconds.
    """
    message = _config_message(config, message)
    return log_time(message, start_time)
