from enum import Enum
from typing import Any, Dict, Iterable, Sequence
from uuid import uuid4

from icon_manager.config.base import Config
from icon_manager.crawler import filters
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.environment import get_converted_env_path
from icon_manager.helpers.resource import user_config_template_file
from icon_manager.interfaces.factory import FileFactory
from icon_manager.interfaces.path import (ConfigFile, IconSearchFolder, PathModel,
                                          SearchFolder)


class UserConfig(Config):

    @classmethod
    def file_name(cls) -> str:
        return '*.config'

    def __init__(self, icons_path: SearchFolder, search_folders: Sequence[IconSearchFolder],
                 code_folders: Iterable[str], exclude_folders: Iterable[str],
                 before_or_after: Iterable[str], copy_icon: bool) -> None:
        super().__init__()
        self.uuid = uuid4()
        self.icons_path = icons_path
        self.search_folders = search_folders
        self.code_folders = code_folders
        self.exclude_folders = exclude_folders
        self.before_or_after = before_or_after
        self.copy_icon = copy_icon

    def validate(self):
        filters.EXCLUDED_FOLDERS = self.exclude_folders
        filters.PROJECT_FOLDERS = self.code_folders

    def search_folder_by(self, entry: PathModel) -> IconSearchFolder:
        for search_folder in self.search_folders:
            if not search_folder.is_path_entry(entry):
                continue
            return search_folder
        raise ValueError(f'Search folder for {entry.path} not exists')


class UserConfigs(str, Enum):
    CONFIG_SECTION = "config"
    CODE_FOLDERS = "code_folders"
    EXCLUDE_FOLDERS = "exclude_folders"
    SEARCH_FOLDERS = "search_folders"
    SEARCH_PATH = "path"
    ICONS_PATH = "icons_path"
    COPY_ICONS = "copy_icon"
    BEFORE_OR_AFTER = "before_or_after"


def get_icons_path(file: ConfigFile, content: Dict[str, Any]) -> SearchFolder:
    icons_path = content.get(UserConfigs.ICONS_PATH, None)
    if icons_path is None:
        raise ValueError(f'Icon path DOES NOT exists in {file.path}')
    return SearchFolder(get_converted_env_path(icons_path))


def get_icons_search_folder(content: Dict[str, Any]) -> IconSearchFolder:
    search_path = content.get(UserConfigs.SEARCH_PATH, None)
    if search_path is None:
        raise ValueError(f'NO path for search folders found')
    search_path = get_converted_env_path(search_path)
    icon_copy = content.get(UserConfigs.COPY_ICONS, None)
    return IconSearchFolder(search_path, icon_copy)


def get_search_folders(file: ConfigFile, content: Dict[str, Any]) -> Sequence[IconSearchFolder]:
    search_folder_configs = content.get(UserConfigs.SEARCH_FOLDERS, None)
    if search_folder_configs is None:
        raise ValueError(f'Search folders DOES NOT exists in {file.path}')
    if not isinstance(search_folder_configs, list) or len(search_folder_configs) == 0:
        raise ValueError(f'Search folders specified in {file.path}')
    search_folders = []
    for folder_config in search_folder_configs:
        if not isinstance(folder_config, dict):
            raise ValueError(f'Search folder config is a list of Dicts')
        icon_search = get_icons_search_folder(folder_config)
        search_folders.append(icon_search)
    return search_folders


class UserConfigFactory(FileFactory[ConfigFile, UserConfig]):

    def __init__(self, source: JsonSource) -> None:
        self.source = source

    def create(self, file: ConfigFile, **kwargs) -> UserConfig:
        content = self.source.read(file, **kwargs)
        content = content.get(UserConfigs.CONFIG_SECTION, {})
        icons_path = get_icons_path(file, content)
        search_folders = get_search_folders(file, content)
        copy_icon = content.get(UserConfigs.COPY_ICONS, False)
        before_or_after = content.get(UserConfigs.BEFORE_OR_AFTER, [])
        code_folders = content.get(UserConfigs.CODE_FOLDERS, [])
        exclude_folders = content.get(UserConfigs.EXCLUDE_FOLDERS, [])
        return UserConfig(icons_path, search_folders,
                          code_folders, exclude_folders,
                          before_or_after, copy_icon)

    def copy_user_config_template(self, user_config: ConfigFile) -> None:
        template_config = user_config_template_file()
        template_config.copy_to(user_config)

    def prepare_template(self, user_config: ConfigFile) -> None:
        content = self.source.read(user_config)
        if content is None:
            raise RuntimeError('Should not be possible')
        chaining_configs = [
            UserConfigs.SEARCH_FOLDERS,
            UserConfigs.BEFORE_OR_AFTER,
            UserConfigs.ICONS_PATH,
            UserConfigs.COPY_ICONS
        ]
        configs = content.get(UserConfigs.CONFIG_SECTION, {})
        for section, values in configs.items():
            if section not in chaining_configs:
                continue
            if isinstance(values, str):
                content[UserConfigs.CONFIG_SECTION][section] = ''
            elif isinstance(values, list):
                content[UserConfigs.CONFIG_SECTION][section] = []
            elif isinstance(values, bool):
                content[UserConfigs.CONFIG_SECTION][section] = False
            else:
                content[UserConfigs.CONFIG_SECTION].pop(section)
        self.source.write(user_config, content)

    def create_template(self, user_config: ConfigFile) -> ConfigFile:
        self.copy_user_config_template(user_config)
        self.prepare_template(user_config)
        return user_config
