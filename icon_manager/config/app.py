import copy
import logging
import os
from collections.abc import Collection, Iterable, Sequence
from enum import Enum
from typing import Any

from icon_manager.config.base import Config
from icon_manager.config.user import UserConfig, UserConfigFactory
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.environment import get_converted_env_path
from icon_manager.helpers.path import get_files, get_path, get_paths
from icon_manager.helpers.resource import app_config_template_file
from icon_manager.helpers.user_inputs import (
    ask_user,
    ask_user_for_path,
    ask_user_yes_no_question,
)
from icon_manager.interfaces.factory import FileFactory
from icon_manager.interfaces.path import ConfigFile, JsonFile
from icon_manager.rules.factory.manager import ExcludeManagerFactory
from icon_manager.rules.manager import ExcludeManager

log = logging.getLogger(__name__)


class AppConfig(Config):
    def __init__(
        self,
        user_configs: Iterable[UserConfig],
        exclude_rules: ExcludeManager,
        before_or_after: Iterable[str],
    ) -> None:
        super().__init__()
        self._exclude_rules = exclude_rules
        self.user_configs = user_configs
        self.before_or_after = before_or_after

    def create_exclude_rules(self) -> ExcludeManager:
        rule_copy = copy.deepcopy(self._exclude_rules)
        return rule_copy

    def validate(self):
        for user_config in self.user_configs:
            user_config.validate()


class AppConfigs(str, Enum):
    USER_CONFIGS = "user_configs"
    BEFORE_OR_AFTER = "before_or_after"


class AppConfigFactory(FileFactory[ConfigFile, AppConfig]):
    APP_CONFIG_NAME = "app_config.config"
    EXCLUDE_NAME = "excluded_rules.config"

    @classmethod
    def app_config_path(cls, folder_path: str = "%APPDATA%/Icon-Manager") -> str:
        folder_path = get_converted_env_path(folder_path)
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        return os.path.join(folder_path, cls.APP_CONFIG_NAME)

    @classmethod
    def app_config_file(cls, folder_path: str = "%APPDATA%/Icon-Manager") -> ConfigFile:
        file_path = cls.app_config_path(folder_path)
        config_file = ConfigFile(file_path)
        return config_file

    @classmethod
    def is_user_config_name(cls, name: str) -> bool:
        return cls.APP_CONFIG_NAME != name and cls.EXCLUDE_NAME != name

    @classmethod
    def get_user_config_paths(cls, folder_path: str) -> Collection[str]:
        names = get_files(folder_path, ConfigFile.extension())
        names = list(filter(lambda name: cls.is_user_config_name(name), names))
        return get_paths(folder_path, names)

    @classmethod
    def get_exclude_config(cls, folder_path: str) -> str | None:
        names = get_files(folder_path, ConfigFile.extension())
        names = list(filter(lambda name: cls.EXCLUDE_NAME == name, names))
        if len(names) != 1:
            return None
        return get_path(folder_path, names[0])

    def __init__(self, source: JsonSource, factory: ExcludeManagerFactory) -> None:
        self.source = source
        self.user_factory = UserConfigFactory(source)
        self.excluded_factory = factory

    def _get_user_config_paths(self, config_folder: str) -> Collection[str]:
        return self.__class__.get_user_config_paths(config_folder)

    def _get_exclude_config_path(self, config_folder: str) -> str | None:
        return self.__class__.get_exclude_config(config_folder)

    def is_user_config_path_empty(self, config_folder: str) -> bool:
        return len(config_folder) == 0

    def does_user_config_path_exists(self, config_folder: str) -> bool:
        return os.path.isdir(config_folder)

    def does_user_configs_exists(self, config_folder: str) -> bool:
        config_files = self._get_user_config_paths(config_folder)
        return len(config_files) > 0

    def ask_user_for_config_path(self, information: str | None) -> str:
        message = "Please enter path for all user configurations: "
        config_path = ask_user_for_path(message, information)
        return get_converted_env_path(config_path)

    def ask_user_for_config_file_name(self) -> str:
        message = "Enter new user configuration file name (/wo extension) "
        file_name = ask_user(message)
        if len(file_name) == 0:
            return self.ask_user_for_config_file_name()
        return file_name

    def ask_user_if_not_any_config_file_exist(self, folder_path: str) -> None:
        message = f'Not any config file exists in\n"{folder_path}":\nChange path y / n: '
        change_folder = ask_user_yes_no_question(message)
        if change_folder:
            folder_path = self.ask_user_for_config_path(information=None)
        if not self.does_user_configs_exists(folder_path):
            self.create_user_template_config(folder_path)
        if not self.does_excluded_rules_template_exists(folder_path):
            self.create_excluded_rules_template(folder_path)

    def create_user_template_config(self, folder_path: str) -> None:
        file_name = self.ask_user_for_config_file_name()
        file_path = get_path(folder_path, file_name)
        user_config = ConfigFile(file_path)
        self.user_factory.create_template(user_config)

    def does_excluded_rules_template_exists(self, config_folder: str) -> bool:
        config_file = self._get_exclude_config_path(config_folder)
        return config_file is not None

    def create_excluded_rules_template(self, path: str) -> None:
        file_path = get_path(path, self.__class__.EXCLUDE_NAME)
        config = ConfigFile(file_path)
        if config.exists():
            return
        self.excluded_factory.create_template(config)

    def create_user_configs(self, content: dict[str, Any]) -> Sequence[UserConfig]:
        config_folder_path = content[AppConfigs.USER_CONFIGS]
        user_configs = []
        for config_file_path in self._get_user_config_paths(config_folder_path):
            user_config_file = ConfigFile(config_file_path)
            user_config = self.user_factory.create(user_config_file)
            if not user_config.has_search_folders():
                config_name = user_config_file.name_wo_extension
                message = f'No valid search folder in "{config_name}" []'
                log.warning(message)
                continue
            user_configs.append(user_config)
        return user_configs

    def create_exclude_config(self, content: dict[str, Any]) -> ExcludeManager:
        config_folder = content[AppConfigs.USER_CONFIGS]
        config_path = self._get_exclude_config_path(config_folder)
        if config_path is None:
            return ExcludeManager([])
        return self.excluded_factory.create(JsonFile(config_path))

    def create(self, file: ConfigFile, **kwargs) -> AppConfig:
        if not file.exists():
            template_file = app_config_template_file()
            template_file.copy_to(file)
        content = self.source.read(file, **kwargs)
        config_folder_path = content.get(AppConfigs.USER_CONFIGS, "")
        if self.is_user_config_path_empty(config_folder_path):
            information = "No path for the user configuration exists"
            config_folder_path = self.ask_user_for_config_path(information)
        elif not self.does_user_config_path_exists(config_folder_path):
            information = f'The saved path does NOT exists\n"{config_folder_path}"'
            config_folder_path = self.ask_user_for_config_path(information)
        if not self.does_user_configs_exists(config_folder_path):
            self.ask_user_if_not_any_config_file_exist(config_folder_path)
        content[AppConfigs.USER_CONFIGS] = config_folder_path
        self.source.write(file, content)
        user_configs = self.create_user_configs(content)
        if len(user_configs) == 0:
            raise ValueError("No valid user configuration exists")
        exclude_rules = self.create_exclude_config(content)
        before_or_after = content.get(AppConfigs.BEFORE_OR_AFTER, [])
        return AppConfig(user_configs, exclude_rules, before_or_after)
