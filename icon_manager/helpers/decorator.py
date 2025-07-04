import logging
from datetime import datetime

from icon_manager.helpers.logs import log_begin, log_end, log_ending

log = logging.getLogger(__name__)


def execution(message, start_message=None):
    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            config = getattr(self, "user_config", None)
            if start_message is not None:
                log.info(log_begin(config, start_message, start_time))
            result = func(self, *args, **kwargs)
            log.info(log_end(config, message, start_time))
            return result

        return execution_time

    return actual_decorator


def crawler_result(message, start_message=None):
    def actual_decorator(func):
        def execution_time(self, *args, **kwargs):
            start_time = datetime.now()
            config = getattr(self, "user_config", None)
            if start_message is not None:
                log.info(log_begin(config, start_message, start_time))
            result = func(self, *args, **kwargs)
            log.info(log_ending(result, message, start_time))
            return result

        return execution_time

    return actual_decorator
