import argparse

from icon_manager.config.config import AppConfig
from icon_manager.config.creator import ConfigCreator
from icon_manager.data.json_source import JsonSource
from icon_manager.services.icon_manager import IconFolderService
from icon_manager.utils.resources import folder_config_path


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
    parser.add_argument('--folders-config', '-f', dest='folders_config', action='store',
                        default=folder_config_path(), help='Absolute Path to JSON file with folders configuration')
    parser.add_argument('--remove-existing', '-r', action='store_true',
                        help='Absolute Path to export the app configuration as a template')
    parser.add_argument('--export-config', '-e', action='store_true',
                        help='Create icon config files for every existing icon file')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='Overwrite existing configs (icon-json & desktop.ini)')
    parser.add_argument('--update', '-u', action='store_true',
                        help='Update rules and template section in exiting icon configs')
    return parser.parse_args()


def get_config(namespace: argparse.Namespace) -> AppConfig:
    manager = AppConfig(get_folder_file(namespace))
    manager.read_config(JsonSource())
    manager.validate()
    return manager


def get_service(namespace: argparse.Namespace) -> IconFolderService:
    config = get_config(namespace)
    service = IconFolderService(config)
    return service


def main():
    namespace = get_namespace_from_args()
    service = get_service(namespace)

    if namespace.export_config:
        overwrite = namespace.overwrite
        update = namespace.update
        service.export_config_templates(overwrite, update)

    if namespace.remove_existing:
        service.remove_existing_configs()

    if namespace.add_icons:
        service.read_config()
        service.collect_folder_to_add_icons()
        creator = ConfigCreator()
        with_error = service.add_icons_to_folders(creator)
        for folder in with_error:
            print(folder.error_message())


if __name__ == "__main__":
    main()
