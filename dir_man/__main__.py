import argparse
import os
from typing import Iterable

from dir_man.data.json_reader import JsonReader
from dir_man.models.container import FolderContainer, SearchOption
from dir_man.models.path import JsonFile
from dir_man.services.manager import FolderManager, WriteConfigManager

EXCLUDE_PATHS: Iterable[str] = [
    '__pycache__', '.mypy_cache', 'bin', 'obj'
]

STOP_SEARCH: Iterable[str] = [
    '.git', '.svn', '.venv', '.vs', '.vscode',
]

SEARCH_OPTIONS = SearchOption(STOP_SEARCH, EXCLUDE_PATHS)

FOLDER_PATHS = [
    FolderContainer('C:\\workspace', SEARCH_OPTIONS),
    FolderContainer('C:\\Users\\erasc\\OneDrive\\workspace', SEARCH_OPTIONS),
    FolderContainer('C:\\Users\\erasc\\OneDrive\\Develop', SEARCH_OPTIONS),
    FolderContainer('C:\\Users\\erasc\\OneDrive\\Software', SEARCH_OPTIONS)
]


def default_config_path() -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), 'resources']
    paths.append('icon_config.json')
    return os.path.join(*paths)


def default_config() -> JsonFile:
    return JsonFile(default_config_path())


def args_description() -> argparse.Namespace:
    description = 'Helper to add icons to folders defined in a external JSON file.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--config', '-c', nargs=1, metavar='N', type=str,
                        help='Absolute Path to JSON file with icon / folder mapping')
    parser.add_argument('--folders', '-f', dest='folder_config', action='store',
                        default=,
                        help='sum the integers (default: find the max)')
    return parser.parse_args()


print(args.accumulate(args.integers))


def main():
    reader = JsonReader()
    config = reader.read_file(CONFIG_FILE)
    manager = FolderManager()
    manager.remove_existing_models(FOLDER_PATHS)
    manager.read_config(config)
    manager.collect_folder_to_add_icons(FOLDER_PATHS)
    writer = WriteConfigManager()
    with_error = manager.add_icons_to_folders(writer)
    for folder in with_error:
        print(folder.error_message())


if __name__ == "__main__":
    main()
