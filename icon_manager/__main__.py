import argparse
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from icon_manager.config.app import AppConfig, AppConfigFactory
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.logs import log_time
from icon_manager.helpers.resource import app_config_template_file
from icon_manager.interfaces.path import ConfigFile
from icon_manager.rules.factory.manager import ExcludeManagerFactory
from icon_manager.services.app_service import IconsAppService

log = logging.getLogger(__name__)


def console(level) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    # format_string = '%(levelname)-8s: %(name)-12s: %(funcName)s - %(message)s'
    # format_string = '%(levelname)-8s %(funcName)-30s>> %(message)s'
    format_string = "%(levelname)-8s  %(message)s"
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    return handler


def log_file(level) -> logging.Handler:
    file_path = os.path.join(os.getcwd(), "icon_manager.log")
    handler = RotatingFileHandler(filename=file_path, mode="a", maxBytes=10240, backupCount=3, encoding="UTF-8")
    handler.setLevel(level)
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    #                               '%d-%b-%y %H:%M:%S')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", "%d-%b-%y %H:%M:%S")
    handler.setFormatter(formatter)
    return handler


def config_logger(level):
    logging.basicConfig(handlers=[console(level)], level=level)
    logger = logging.getLogger("Icon Manager Logger")
    # logger.addHandler(log_file(logging.DEBUG))
    logger.info("Logger configured")


def get_namespace_from_args() -> argparse.Namespace:
    description = "Helper to add icons to folders defined in a external JSON file."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--library",
        "-l",
        action="store_true",
        help="Execute the options on icon library",
    )
    parser.add_argument(
        "--content",
        "-c",
        action="store_true",
        help="Execute the options on search contents",
    )
    # Options
    parser.add_argument(
        "--create",
        "-a",
        action="store_true",
        help="Creates the library configs or applies the icons to folders",
    )
    parser.add_argument(
        "--re-create",
        "-r",
        action="store_true",
        help="Re apply the icons to the folder. The icons get lost over OneDrive synchronization",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Updates library configs with the content of the template",
    )
    parser.add_argument(
        "--delete",
        "-d",
        action="store_true",
        help="Deletes the library configs or applied icons",
    )
    parser.add_argument(
        "--archive",
        "-v",
        action="store_true",
        help='Moves the library configs without rules into subfolder "archive"',
    )
    return parser.parse_args()


def get_app_config(config_file: ConfigFile) -> AppConfig:
    exclude_factory = ExcludeManagerFactory(JsonSource())
    factory = AppConfigFactory(JsonSource(), exclude_factory)
    config = factory.create(config_file)
    config.validate()
    return config


def get_service() -> IconsAppService:
    app_config = AppConfigFactory.app_config_file()
    if not app_config.exists():
        app_template = app_config_template_file()
        app_template.copy_to(app_config)
    app_config = get_app_config(app_config)
    service = IconsAppService(app_config)
    return service


def main():
    config_logger(logging.INFO)
    namespace = get_namespace_from_args()
    start_time = datetime.now()
    service = get_service()
    service.setup()

    service.create_settings()
    if namespace.library:
        if namespace.delete:
            service.delete_library_configs()
        if namespace.update:
            service.update_library_configs()
        elif namespace.create:
            service.create_library_configs()
        if namespace.archive:
            service.archive_icons_and_configs()
    elif namespace.content:
        service.setup_and_merge_user_service()
        if namespace.delete or namespace.re_create:
            service.async_find_existing_content()
        if namespace.delete:
            service.async_delete_icon_settings()
        if namespace.re_create:
            service.re_apply_matched_icons()
        if namespace.create:
            service.async_find_and_apply_matches()
    log.info(log_time("Execution-Time".upper(), start_time))


if __name__ == "__main__":
    main()
