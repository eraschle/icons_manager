import logging
from datetime import datetime

from icon_manager.helpers.string import ALIGN_LEFT, ALIGN_RIGHT, fixed_length

log = logging.getLogger(__name__)


def get_time_log(message: str, width: int = 12) -> str:
    return fixed_length(message, width=width, align=ALIGN_RIGHT)


def get_time_msg(start: datetime) -> str:
    diff = (datetime.now() - start).total_seconds()
    return get_time_log(f"{diff: .2f} sec")


def log_time(message: str, start: datetime) -> str:
    return f"{message} in {get_time_msg(start)}"


def _config_message(
    config_name: str | None,
    message: str,
    width_config: int = 20,
    width_message: int = 60,
):
    name = fixed_length(config_name or "", width=width_config, align=ALIGN_LEFT)
    log_message = fixed_length(message, width=width_message, align=ALIGN_LEFT)
    return f"{name}: {log_message}"


def log_begin(config_name: str | None, message: str, start_time: datetime):
    message = _config_message(config_name, message)
    start_value = start_time.strftime("%H:%M:%S")
    return f"{message} at {get_time_log(start_value)}"


def log_end(config_name: str | None, message: str, start_time: datetime):
    message = _config_message(config_name, message)
    return log_time(message, start_time)
