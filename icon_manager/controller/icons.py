import logging
from typing import Iterable, List, Optional, Tuple

from icon_manager.config.config import AppConfig
from icon_manager.controller.base import FileBaseController
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.resource import icon_config_template
from icon_manager.managers.find import File, FindOptions, Folder
from icon_manager.models.config import IconConfig
from icon_manager.models.path import ArchiveFolder, FileModel, IconFile, JsonFile
from icon_manager.services.factories import ConfigFactory

log = logging.getLogger(__name__)


class IconsController(FileBaseController[IconFile]):

    def __init__(self, config: AppConfig) -> None:
        super().__init__(config.icons_path(), IconFile)
        self.config_factory = ConfigFactory(config.rule_mapping(),
                                            config.before_or_after_values(),
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
        template = icon_config_template()
        for icon_file in self.get_files():
            icon_config = self.get_config_path(icon_file)
            if not overwrite and icon_config.exists():
                continue
            template.copy_to(icon_config)
            log.info(f'Exported config for {icon_file.name_wo_extension}')

    def update_icon_config_files(self):
        source = JsonSource()
        template = icon_config_template()
        template_config = source.read(template)
        for config_file in self.get_config_files():
            config = source.read(config_file)
            for section, values in template_config.items():
                if section == 'config':
                    continue
                if config[section] == values:
                    continue
                config[section] = values
            source.write(config_file, config)
            log.info(f'Updated config {config_file.name_wo_extension}')

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

    def create_icon_config(self, remove_empty: bool = True) -> None:
        configs = []
        json_reader = JsonSource()
        for icon_file, config_file in self.icon_and_config_files():
            config_dict = json_reader.read(config_file)
            icon_config = self.config_factory.create(config_dict,
                                                     icon_file=icon_file)
            if icon_config.is_empty() and remove_empty:
                continue
            configs.append(icon_config)
        self.icon_configs = sorted(configs, key=lambda cnf: cnf.order_key())


# region ARCHIVE EMPTY ICON CONFIG


    def archive_empty_icon_configs(self):
        for icon_config in self.icon_configs:
            if not icon_config.is_empty():
                continue
            self.archive_icon_config(icon_config)

    def get_archive_folder(self, icon_config: IconConfig):
        icon_file = icon_config.icon_file
        folder_path = ArchiveFolder.get_folder_path(icon_file)
        folder = ArchiveFolder(folder_path)
        if not folder.exists():
            folder.create()
        return folder

    def archive_icon_config(self, config: IconConfig):
        folder = self.get_archive_folder(config)
        self.archive_icon_file(config, folder)
        self.archive_config_file(config, folder)

    def archive_icon_file(self, config: IconConfig, folder: ArchiveFolder):
        icon_file = config.icon_file
        archive = folder.icon_archive(icon_file)
        self.archive_file(icon_file, archive)

    def archive_config_file(self, config: IconConfig, folder: ArchiveFolder):
        config_file = config.config_file()
        archive = folder.icon_archive(config_file)
        self.archive_file(config_file, archive)

    def archive_file(self, file: FileModel, archive: FileModel):
        file.copy_to(archive)
        log.info(f'{file.name} archived to {archive.path}')
        file.remove()


# endregion
