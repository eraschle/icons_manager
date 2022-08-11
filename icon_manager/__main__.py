import argparse
from distutils.command.config import config
import os
import sys
from typing import Optional
from icon_manager.config.config import ConfigManager

from icon_manager.data.json_source import JsonSource
from icon_manager.models.path import JsonFile
from icon_manager.services.icon_folders import IconFolderService, WriteConfigManager


def get_icons_path() -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), 'resources']
    paths.append('icons_config.json')
    return os.path.join(*paths)


def get_icons_file(namespace: argparse.Namespace) -> JsonFile:
    file_path = namespace.icons_config
    if file_path is None:
        return JsonFile(get_icons_path())
    return JsonFile(file_path)


def get_folders_path() -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), 'resources']
    paths.append('folders_config.json')
    return os.path.join(*paths)


def get_folder_file(namespace: argparse.Namespace) -> JsonFile:
    file_path = namespace.folders_config
    if file_path is None:
        return JsonFile(get_folders_path())
    return JsonFile(file_path)


def get_namespace_from_args() -> argparse.Namespace:
    description = 'Helper to add icons to folders defined in a external JSON file.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--folders-config', '-f', dest='folders_config', action='store',
                        default=get_folders_path(),
                        help='Absolute Path to JSON file with folders configuration')
    parser.add_argument('--icons-config', '-i', dest='icons_config', action='store',
                        default=get_icons_path(),
                        help='Absolute Path to JSON file with icons configuration')
    parser.add_argument('--remove-existing', '-r', dest='remove_existing', action='store',
                        default=False,
                        help='Absolute Path to export the app configuration as a template')
    parser.add_argument('--export-config', '-e', dest='export_path', action='store',
                        default=None,
                        help='Absolute Path to export the configuration as a template')
    return parser.parse_args()


def get_config(namespace: argparse.Namespace) -> ConfigManager:
    manager = ConfigManager(get_icons_file(namespace),
                            get_folder_file(namespace))
    manager.load_config(JsonSource())
    manager.validate()
    return manager


def get_service(namespace: argparse.Namespace) -> IconFolderService:
    config = get_config(namespace)
    service = IconFolderService(config)
    return service


def main(*args):
    namespace = get_namespace_from_args()
    service = get_service(namespace)

    if namespace.export_path is not None:
        service.export_template_config(namespace.export_path)

    if namespace.remove_existing:
        service.remove_existing_models()

    elif service.can_add_icons_to_folders():
        service.read_config()
        service.collect_folder_to_add_icons()
        writer = WriteConfigManager()
        with_error = service.add_icons_to_folders(writer)
        for folder in with_error:
            print(folder.error_message())


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
