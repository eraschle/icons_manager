from typing import Iterable, Optional, Tuple

from icon_manager.config.config import ConfigManager
from icon_manager.controller.base import BaseController
from icon_manager.data.json_source import JsonSource
from icon_manager.models.config import IconConfig
from icon_manager.models.path import FolderModel, IconFile, JsonFile
from icon_manager.services.factories import ConfigFactory
from icon_manager.tasks.find_folders import FindOptions, FindPathTask
from icon_manager.utils.resources import icon_config_template_file


class IconsController(BaseController[IconFile]):

    def __init__(self, config: ConfigManager) -> None:
        super().__init__(config.icons_path(), IconFile)
        self.config_factory = ConfigFactory(config.rule_mapping())
        self.icon_configs: Iterable[IconConfig] = []

    def is_folder_excluded(self, value: str) -> bool:
        return FindOptions.default_excluded(value) and value not in ['_check']

    def get_find_options(self) -> FindOptions:
        options = super().get_find_options()
        options.is_folder_excluded = self.is_folder_excluded
        return options

    def get_config_path(self, icon: IconFile) -> JsonFile:
        file_path = icon.path
        file_path = file_path.replace(IconFile.extension(),
                                      JsonFile.extension())
        return JsonFile(file_path)

    def create_icon_config_files(self, overwrite: bool):
        template = icon_config_template_file()
        for icon_file in self.files():
            icon_config = self.get_config_path(icon_file)
            if not overwrite and icon_config.exists():
                continue
            template.copy_to(icon_config)

    def get_config_find_options(self) -> FindOptions:
        options = self.get_find_options()
        options.is_file_allowed = JsonFile.is_model
        return options

    def get_icon_configs(self) -> Iterable[JsonFile]:
        options = self.get_config_find_options()
        find_task = FindPathTask(self.full_path, options)
        config_files = [JsonFile(path) for path in find_task.files()]
        return config_files

    def icon_and_config_files(self) -> Iterable[Tuple[IconFile, JsonFile]]:
        return zip(self.files(), self.get_icon_configs())

    def create_icon_config(self) -> None:
        configs = []
        json_reader = JsonSource()
        for icon_file, config_file in self.icon_and_config_files():
            config_dict = json_reader.read_file(config_file)
            icon_config = self.config_factory.create(config_dict,
                                                     icon_file=icon_file)
            if icon_config.is_empty():
                continue
            configs.append(icon_config)
        self.icon_configs = sorted(configs, key=lambda cnf: cnf.order_key())

    def icon_config_for(self, folder: FolderModel) -> Optional[IconConfig]:
        for config in self.icon_configs:
            if not config.is_config_for(folder):
                continue
            return config
        return None
