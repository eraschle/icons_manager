
import os

from icon_manager.models.path import JsonFile


def __resources_path(file_name: str) -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), '..', 'resources']
    paths.append(file_name)
    return os.path.join(*paths)


def icons_config_path() -> str:
    return __resources_path('icons_config.json')


def icon_config_template_path() -> str:
    return __resources_path('icon_config_template.json')


def icon_config_template_file() -> JsonFile:
    return JsonFile(icon_config_template_path())


def folder_config_path() -> str:
    return __resources_path('folders_config.json')
