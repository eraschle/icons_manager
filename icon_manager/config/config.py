import os
import re
from typing import Any, Collection, Dict, Iterable, Protocol, Type

from icon_manager.controller.search import SearchController
from icon_manager.source.json_source import JsonSource
from icon_manager.models.path import JsonFile
from icon_manager.models.rules import (ChainedRules, ContainsRule,
                                       EndswithRule, EqualsRule, FilterRule,
                                       NotContainsRule, NotEqualsRule,
                                       StartsOrEndswithRule, StartswithRule)


class Config(Protocol):

    def read_config(self, config: Dict[str, Any]):
        ...

    def validate(self):
        ...


class FolderConfig(Config):
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

    def __init__(self, config_file: JsonFile) -> None:
        super().__init__()
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.icons_path: str = ''
        self.code_project_names: Iterable[str] = []
        self.exclude_folder_names: Iterable[str] = []
        self.folder_paths: Iterable[str] = []

    def read_config(self, reader: JsonSource):
        self.config = reader.read(self.config_file)

    def validate(self):
        icons_path = self.config.pop('icons_path', None)
        if icons_path is None:
            raise ValueError('Icon path could not be found')
        self.icons_path = self.__class__.get_folder_path(icons_path)
        self.copy_icon = self.config.get('copy_icon', False)
        code_project_names = self.config.pop('code_project_names', [])
        exclude_folder_names = self.config.pop('exclude_folder_names', [])
        folder_paths = self.config.pop('folder_paths', None)
        if folder_paths is None:
            raise ValueError('No directories specified to set the icons')
        self.code_project_names = code_project_names
        self.exclude_folder_names = exclude_folder_names
        self.folder_paths = folder_paths

    def get_search_folder_paths(self) -> Collection[str]:
        containers = []
        for folder_path in self.folder_paths:
            folder_path = self.__class__.get_folder_path(folder_path)
            containers.append(folder_path)
        return containers


RULE_MAP: Dict[str, Type[FilterRule]] = {
    'equals': EqualsRule,
    "not_equals": NotEqualsRule,
    "starts_with": StartswithRule,
    "ends_with": EndswithRule,
    "start_or_ends_with": StartsOrEndswithRule,
    'contains': ContainsRule,
    'not_contains': NotContainsRule,
    'chained': ChainedRules
}


class AppConfig(Config):

    def __init__(self, config_file: JsonFile) -> None:
        self.folders = FolderConfig(config_file)

    def read_config(self, reader: JsonSource):
        self.folders.read_config(reader)

    def validate(self):
        self.folders.validate()
        SearchController.project_folder_names = self.folders.code_project_names
        SearchController.excluded_folder_names = self.folders.exclude_folder_names

    def copy_icon_to_folder(self) -> bool:
        return self.folders.copy_icon

    def icons_path(self) -> str:
        return self.folders.icons_path

    def search_folder_paths(self) -> Collection[str]:
        return self.folders.get_search_folder_paths()

    def rule_mapping(self) -> Dict[str, Type[FilterRule]]:
        return RULE_MAP
