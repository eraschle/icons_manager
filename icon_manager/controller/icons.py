from typing import Iterable, List, Optional, Tuple

from icon_manager.config.config import AppConfig
from icon_manager.controller.base import FileBaseController
from icon_manager.data.json_source import JsonSource
from icon_manager.models.config import IconConfig
from icon_manager.models.path import IconFile, JsonFile
from icon_manager.services.factories import ConfigFactory
from icon_manager.tasks.find_folders import File, FindOptions, Folder
from icon_manager.utils.resources import icon_config_template_file


class IconsController(FileBaseController[IconFile]):

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config.icons_path(), IconFile)
        self.config_factory = ConfigFactory(config.rule_mapping(),
                                            config.copy_icon_to_folder())
        self.icon_configs: Iterable[IconConfig] = []
        self.config_files: List[JsonFile] = []

    def check_folder_excluded(self, value: str) -> bool:
        return value in ['_check']

    def get_find_options(self) -> FindOptions:
        options = super().get_find_options()
        options.add_file_allowed(JsonFile.is_model)
        options.add_folder_excluded(self.check_folder_excluded)
        return options

    def create_files(self, folders: Iterable[Folder], files: Iterable[File]) -> Iterable[IconFile]:
        for file in files:
            if not JsonFile.is_model(file.full_path):
                continue
            self.config_files.append(JsonFile(file.full_path))
        return super().create_files(folders, files)

    def get_config_path(self, icon: IconFile) -> JsonFile:
        file_path = icon.path
        file_path = file_path.replace(IconFile.extension(),
                                      JsonFile.extension())
        return JsonFile(file_path)

    def create_icon_config_files(self, overwrite: bool):
        template = icon_config_template_file()
        for icon_file in self.get_files():
            icon_config = self.get_config_path(icon_file)
            if not overwrite and icon_config.exists():
                continue
            template.copy_to(icon_config)

    def update_icon_config_files(self):
        source = JsonSource()
        template = icon_config_template_file()
        template_config = source.read(template.path)
        for config_file in self.get_config_files():
            config = source.read(config_file.path)
            for section, values in template_config.items():
                if section == 'config':
                    continue
                config[section] = values
            source.write(config_file.path, config)

    def config_by_name(self, icon_file: IconFile) -> Optional[JsonFile]:
        for config_file in self.config_files:
            if config_file.name_wo_extension != icon_file.name_wo_extension:
                continue
            return config_file
        return None

    def get_config_files(self) -> Iterable[JsonFile]:
        config_files = []
        for icon_file in self.get_files():
            config_file = self.config_by_name(icon_file)
            if config_file is None:
                continue
            config_files.append(config_file)
        return config_files

    def icon_and_config_files(self) -> Iterable[Tuple[IconFile, JsonFile]]:
        return zip(self.get_files(), self.get_config_files())

    def create_icon_config(self) -> None:
        configs = []
        json_reader = JsonSource()
        for icon_file, config_file in self.icon_and_config_files():
            config_dict = json_reader.read(config_file.path)
            icon_config = self.config_factory.create(config_dict,
                                                     icon_file=icon_file)
            if icon_config.is_empty():
                continue
            configs.append(icon_config)
        self.icon_configs = sorted(configs, key=lambda cnf: cnf.order_key())
