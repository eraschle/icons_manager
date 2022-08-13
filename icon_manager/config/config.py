import os
import re
from abc import abstractmethod
from typing import Any, Collection, Dict, Iterable, Protocol, Type

from icon_manager.controller.search import SearchController
from icon_manager.data.json_source import JsonSource
from icon_manager.models.container import FolderContainer
from icon_manager.models.path import JsonFile
from icon_manager.models.rules import (ChainedRules, ContainsRule, EqualsRule,
                                       FilterRule, NotContainsRule)


class Config(Protocol):

    def load_config(self, config: Dict[str, Any]):
        ...

    def validate(self):
        ...


class AppConfig(Config):
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}

    def load_config(self, config: Dict[str, Any]):
        self.config.update(config)

    @abstractmethod
    def validate(self):
        ...


class IconConfig(AppConfig):
    def __init__(self) -> None:
        super().__init__()
        self.copy_icon: bool = False

    def validate(self):
        self.copy_icon = self.config.get('copy_icon', False)

    def folder_configs(self) -> Dict[str, Dict[str, Any]]:
        self.config.pop('copy_icon', None)
        return self.config


class FolderConfig(AppConfig):
    env_pattern = re.compile(r'(?P<env>%[a-zA-Z0-9_-]*%)')

    @classmethod
    def get_folder_path(cls, folder_path: str) -> str:
        matches = cls.env_pattern.match(folder_path)
        if matches is None:
            return folder_path
        match_value = matches.groupdict().get('env', None)
        if match_value is None:
            return folder_path
        env_key = match_value[1:-1]
        env_value = os.getenv(env_key, None)
        if env_value is None:
            return folder_path
        return folder_path.replace(match_value, env_value)

    def __init__(self) -> None:
        super().__init__()
        self.icons_path: str = ''
        self.code_project_names: Iterable[str] = []
        self.exclude_folder_names: Iterable[str] = []
        self.folder_paths: Iterable[str] = []

    def load_config(self, config: Dict[str, Any]):
        super().load_config(config)

    def validate(self):
        icons_path = self.config.pop('icons_path', None)
        if icons_path is None:
            raise ValueError('Icon path could not be found')
        self.icons_path = self.__class__.get_folder_path(icons_path)
        code_project_names = self.config.pop('code_project_names', [])
        exclude_folder_names = self.config.pop('exclude_folder_names', [])
        folder_paths = self.config.pop('folder_paths', None)
        if folder_paths is None:
            raise ValueError('No directories specified to set the icons')
        self.code_project_names = code_project_names
        self.exclude_folder_names = exclude_folder_names
        self.folder_paths = folder_paths

    def get_folder_containers(self) -> Collection[FolderContainer]:
        containers = []
        for folder_path in self.folder_paths:
            folder_path = self.__class__.get_folder_path(folder_path)
            containers.append(FolderContainer(folder_path))
        return containers


RULE_MAP: Dict[str, Type[FilterRule]] = {
    'equals': EqualsRule,
    'contains': ContainsRule,
    'not_contains': NotContainsRule,
    'chained': ChainedRules
}


class ConfigManager(Config):

    def __init__(self, icon_file: JsonFile, folder_file: JsonFile) -> None:
        self.folder_config_file = folder_file
        self.folders = FolderConfig()
        self.icon_config_file = icon_file
        self.icons = IconConfig()

    def load_config(self, reader: JsonSource):
        icon_config = reader.read_file(self.icon_config_file)
        icon_config = icon_config.get('config', {})
        self.icons.load_config(icon_config)
        folder_config = reader.read_file(self.folder_config_file)
        self.folders.load_config(folder_config)

    def validate(self):
        self.icons.validate()
        self.folders.validate()
        SearchController.project_folder_names = self.folders.code_project_names
        SearchController.excluded_folder_names = self.folders.exclude_folder_names

    def copy_icon_to_container(self) -> bool:
        return self.icons.copy_icon

    def icons_path(self) -> str:
        return self.folders.icons_path

    def folder_containers(self) -> Collection[FolderContainer]:
        return self.folders.get_folder_containers()

    def rule_mapping(self) -> Dict[str, Type[FilterRule]]:
        return RULE_MAP
