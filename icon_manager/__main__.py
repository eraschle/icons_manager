import argparse
import logging
import os
from logging.handlers import RotatingFileHandler

from icon_manager.services.icon_manager import get_service

log = logging.getLogger(__name__)


def console(level) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    # format_string = '%(levelname)-8s: %(name)-12s: %(funcName)s - %(message)s'
    format_string = '%(levelname)-8s %(funcName)-30s>> %(message)s'
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    return handler


def log_file(level) -> logging.Handler:
    file_path = os.path.join(os.getcwd(), 'icon_manager.log')
    handler = RotatingFileHandler(filename=file_path, mode='a', maxBytes=10240,
                                  backupCount=3, encoding='UTF-8')
    handler.setLevel(level)
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    #                               '%d-%b-%y %H:%M:%S')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                                  '%d-%b-%y %H:%M:%S')
    handler.setFormatter(formatter)
    return handler


def config_logger():
    logging.basicConfig(handlers=[console(logging.INFO)], level=logging.INFO)
    logger = logging.getLogger('Icon Manager Logger')
    # logger.addHandler(log_file(logging.DEBUG))
    logger.info('Logger configured')


def get_namespace_from_args() -> argparse.Namespace:
    description = 'Helper to add icons to folders defined in a external JSON file.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--add_icons', '-a', action='store_true',
                        help='Execute the process to add icons to folders')
    parser.add_argument('--re-write-ini-file', '-r', action='store_true',
                        help='Re write desktop.ini file. The setting are lost after sync with OneDrive')
    parser.add_argument('--delete-folder-config', '-d', action='store_true',
                        help='Absolute Path to export the app configuration as a template')
    parser.add_argument('--create-icon-config', '-i', action='store_true',
                        help='Create icon config files for every existing icon file')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='Overwrite existing configs (icon-json & desktop.ini)')
    parser.add_argument('--update', '-u', action='store_true',
                        help='Update rules and template section in exiting icon configs')
    parser.add_argument('--archive', '-v', action='store_true',
                        help='Move icon with an empty config file into the subfolder "archive"')
    return parser.parse_args()


def main():
    config_logger()
    namespace = get_namespace_from_args()
    service = get_service()

    if namespace.create_icon_config:
        overwrite = namespace.overwrite
        update = namespace.update
        service.create_icon_config_templates(overwrite, update)

    if namespace.delete_folder_config:
        service.delete_icon_folder_configs()

    if namespace.add_icons:
        overwrite = namespace.overwrite
        service.add_icons_to_folders(overwrite)

    if namespace.re_write_ini_file:
        service.re_write_icon_config()

    if namespace.archive:
        service.archive_empty_icon_configs()


if __name__ == "__main__":
    main()
