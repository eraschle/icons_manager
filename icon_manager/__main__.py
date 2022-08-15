import argparse
import logging
import os
from logging.handlers import RotatingFileHandler

from icon_manager.config.config import AppConfig
from icon_manager.models.path import JsonFile
from icon_manager.services.icon_manager import IconFolderService
from icon_manager.source.json_source import JsonSource
from icon_manager.utils.resources import folder_config_path

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
    file_path = os.path.join(os.getcwd(), 'rsrg_bim_sbb.txt')
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
    logger.debug('Logger configured')


def get_folder_file(namespace: argparse.Namespace) -> str:
    file_path = namespace.folders_config
    if file_path is None:
        file_path = folder_config_path()
    return file_path


def get_namespace_from_args() -> argparse.Namespace:
    description = 'Helper to add icons to folders defined in a external JSON file.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--add_icons', '-a', action='store_true',
                        help='Execute the process to add icons to folders')
    parser.add_argument('--app-config', '-c', dest='folders_config', action='store',
                        default=folder_config_path(), help='Absolute Path to JSON file with folders configuration')
    parser.add_argument('--export-app-config', '-e', dest='app_config', action='store',
                        help='Creates the app config template to the given path')
    parser.add_argument('--delete-folder-config', '-d', action='store_true',
                        help='Absolute Path to export the app configuration as a template')
    parser.add_argument('--create-icon-config', '-i', action='store_true',
                        help='Create icon config files for every existing icon file')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='Overwrite existing configs (icon-json & desktop.ini)')
    parser.add_argument('--update', '-u', action='store_true',
                        help='Update rules and template section in exiting icon configs')
    return parser.parse_args()


def get_config(namespace: argparse.Namespace) -> AppConfig:
    config_file = JsonFile(get_folder_file(namespace))
    manager = AppConfig(config_file)
    manager.read_config(JsonSource())
    manager.validate()
    return manager


def get_service(namespace: argparse.Namespace) -> IconFolderService:
    config = get_config(namespace)
    service = IconFolderService(config)
    return service


def main():
    config_logger()
    namespace = get_namespace_from_args()
    service = get_service(namespace)

    if namespace.create_icon_config:
        overwrite = namespace.overwrite
        update = namespace.update
        service.create_icon_config_templates(overwrite, update)

    if namespace.app_config is not None:
        service.export_app_config_template(namespace.app_config)

    if namespace.delete_folder_config:
        service.delete_icon_folder_configs()

    if namespace.add_icons:
        service.read_config()
        overwrite = namespace.overwrite
        service.add_icons_to_folders(overwrite)


if __name__ == "__main__":
    main()
