import os
from enum import Enum
from typing import Collection, Iterable, Optional

from icon_manager.config.base import Config
from icon_manager.config.user import UserConfig, UserConfigFactory
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.environment import get_converted_env_path
from icon_manager.helpers.path import get_files, get_path, get_paths
from icon_manager.helpers.resource import app_config_template_file
from icon_manager.helpers.user_inputs import (ask_user, ask_user_for_path,
                                              ask_user_yes_no_question)
from icon_manager.interfaces.factory import FileFactory
from icon_manager.interfaces.path import ConfigFile


class AppConfig(Config):

    def __init__(self, user_configs: Iterable[UserConfig],
                 before_or_after: Iterable[str]) -> None:
        super().__init__()
        self.user_configs = user_configs
        self.before_or_after = before_or_after

    def validate(self):
        for user_config in self.user_configs:
            user_config.validate()

    def merged_before_or_after(self, config: UserConfig) -> Iterable[str]:
        before_or_after = set(self.before_or_after)
        before_or_after.update(config.before_or_after)
        return before_or_after


class AppConfigs(str, Enum):
    USER_CONFIGS = 'user_configs'
    BEFORE_OR_AFTER = 'before_or_after'


class AppConfigFactory(FileFactory[ConfigFile, AppConfig]):

    APP_CONFIG_NAME = 'app_config.config'

    @classmethod
    def app_config_path(cls, folder_path: str = '%APPDATA%/Icon-Manager') -> str:
        folder_path = get_converted_env_path(folder_path)
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        return os.path.join(folder_path, cls.APP_CONFIG_NAME)

    @classmethod
    def app_config_file(cls, folder_path: str = '%APPDATA%/Icon-Manager') -> ConfigFile:
        file_path = cls.app_config_path(folder_path)
        config_file = ConfigFile(file_path)
        return config_file

    @classmethod
    def get_user_config_paths(cls, folder_path: str) -> Collection[str]:
        names = get_files(folder_path, ConfigFile.extension())
        names = filter(lambda name: cls.APP_CONFIG_NAME != name, names)
        return get_paths(folder_path, names)

    def __init__(self, source: JsonSource) -> None:
        self.source = source
        self.user_config_factory = UserConfigFactory(source)

    def __get_user_config_paths(self, config_folder: str) -> Collection[str]:
        return self.__class__.get_user_config_paths(config_folder)

    def is_user_config_path_empty(self, config_folder: str) -> bool:
        return len(config_folder) == 0

    def does_user_config_path_exists(self, config_folder: str) -> bool:
        return os.path.isdir(config_folder)

    def does_user_configs_exists(self, config_folder: str) -> bool:
        config_files = self.__get_user_config_paths(config_folder)
        return len(config_files) > 0

    def ask_user_for_config_path(self, information: Optional[str]) -> str:
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

    def create_user_template_config(self, folder_path: str) -> None:
        file_name = self.ask_user_for_config_file_name()
        file_path = get_path(folder_path, file_name)
        user_config = ConfigFile(file_path)
        self.user_config_factory.create_template(user_config)

    def create(self, file: ConfigFile, **kwargs) -> AppConfig:
        if not file.exists():
            template_file = app_config_template_file()
            template_file.copy_to(file)
        content = self.source.read(file, **kwargs)
        config_folder_path = content.get(AppConfigs.USER_CONFIGS, '')
        if self.is_user_config_path_empty(config_folder_path):
            information = 'No path for the user configuration exists'
            config_folder_path = self.ask_user_for_config_path(information)
        elif not self.does_user_config_path_exists(config_folder_path):
            information = f'The saved path does NOT exists\n"{config_folder_path}"'
            config_folder_path = self.ask_user_for_config_path(information)
        if not self.does_user_configs_exists(config_folder_path):
            self.ask_user_if_not_any_config_file_exist(config_folder_path)
        content[AppConfigs.USER_CONFIGS] = config_folder_path
        self.source.write(file, content)
        user_configs = []
        for config_file_path in self.__get_user_config_paths(config_folder_path):
            user_config_file = ConfigFile(config_file_path)
            user_config = self.user_config_factory.create(user_config_file)
            user_configs.append(user_config)
        before_or_after = content.get(AppConfigs.BEFORE_OR_AFTER, [])
        return AppConfig(user_configs, before_or_after)
