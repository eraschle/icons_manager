
import os

from icon_manager.models.path import JsonFile


def __resources_path(file_name: str) -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), '..', 'resources']
    paths.append(file_name)
    return os.path.join(*paths)


def icon_config_template_path() -> str:
    return __resources_path('icon_config_template.json')


def icon_config_template() -> JsonFile:
    return JsonFile(icon_config_template_path())


def folder_config_path() -> str:
    return __resources_path('app_config.json')


def folder_config_template() -> JsonFile:
    return JsonFile(folder_config_path())
