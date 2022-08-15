
import os
from pathlib import Path

from icon_manager.models.path import FolderModel, JsonFile


def __resources_path(file_name: str) -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), '..', 'resources']
    paths.append(file_name)
    return os.path.join(*paths)


def __user_path(file_name: str) -> str:
    paths = [str(Path.home()), file_name]
    return os.path.join(*paths)


def icon_config_template_path() -> str:
    return __resources_path('icon_config_template.json')


def icon_config_template() -> JsonFile:
    return JsonFile(icon_config_template_path())


def app_config_and_template_path() -> str:
    return __resources_path('app_config.json')


def app_config_and_template() -> JsonFile:
    return JsonFile(app_config_and_template_path())
