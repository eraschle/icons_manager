import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from icon_manager.helpers.logs import log_begin, log_end
from icon_manager.helpers.string import ALIGN_RIGHT, THOUSAND, list_value

log = logging.getLogger(__name__)


@runtime_checkable
class ExecutionResult(Protocol):
    """A return value that can report what it touched.

    Declared here rather than importing ``interfaces.actions.Action``: a
    logging helper has to sit below what it decorates, and importing the
    action layer made ``helpers`` and ``interfaces`` import each other.
    """

    def execution_summary(self) -> tuple[Sequence[Any], Sequence[Any]]:
        """The files and the folders the call affected."""
        ...


def _config_name(instance: object) -> str | None:
    """The name of the user config the decorated instance belongs to, if any.

    The decorator is applied to controllers and services, which carry a
    ``user_config``; anything else is logged without a name.
    """
    user_config = getattr(instance, "user_config", None)
    return getattr(user_config, "name", None)


def execution(message, start_message=None):
    """Log how long the decorated call took."""

    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            name = _config_name(self)
            if start_message is not None:
                log.info(log_begin(name, start_message, start_time))
            result = func(self, *args, **kwargs)
            log.info(log_end(name, message, start_time))
            return result

        return execution_time

    return actual_decorator


def log_files(files: Sequence, message, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    files_log = list_value(files, width=width, align=align)
    return f"{message} Files: {files_log}"


def log_folders(folders: Sequence, message, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
    folders_log = list_value(folders, width=width, align=align)
    return f"{message} Folders: {folders_log}"


def execution_action(message, start_message=None):
    """Log how long the decorated call took, and what its result affected."""

    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            name = _config_name(self)
            if start_message is not None:
                log.info(log_begin(name, start_message, start_time))
            result = func(self, *args, **kwargs)
            log_msg = message
            if isinstance(result, ExecutionResult):
                files, folders = result.execution_summary()
                if len(files) > 0:
                    log_msg = log_files(files, log_msg)
                if len(folders) > 0:
                    log_msg = log_folders(folders, log_msg)
            log.info(log_end(name, log_msg, start_time))
            return result

        return execution_time

    return actual_decorator
