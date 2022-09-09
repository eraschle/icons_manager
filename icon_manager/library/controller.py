import copy
import logging
from typing import Dict, Iterable, List, Optional, Sequence

from icon_manager.content.models.matched import IconSetting
from icon_manager.helpers.path import File
from icon_manager.helpers.resource import icon_setting_template
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import FileCrawlerBuilder, ModelBuilder
from icon_manager.interfaces.controller import ILibraryController
from icon_manager.interfaces.path import FileModel, JsonFile, PathModel
from icon_manager.library.models import (ArchiveFolder, IconFile,
                                         LibraryIconFile)
from icon_manager.rules.factory.manager import RuleManagerFactory
from icon_manager.rules.manager import RuleManager

log = logging.getLogger(__name__)


class RuleManagerBuilder(FileCrawlerBuilder[RuleManager]):

    def __init__(self, factory: RuleManagerFactory = RuleManagerFactory()) -> None:
        self.factory = factory

    def can_build_file(self, file: File, **kwargs) -> bool:
        return JsonFile.is_model(file.path)

    def build_file_model(self, file: File, **kwargs) -> Optional[RuleManager]:
        return self.factory.create(JsonFile(file.path))


class LibraryIconFileBuilder(FileCrawlerBuilder[LibraryIconFile]):

    def can_build_file(self, file: File, **kwargs) -> bool:
        return LibraryIconFile.is_model(file.name)

    def build_file_model(self, file: File, **kwargs) -> Optional[LibraryIconFile]:
        return LibraryIconFile(file.path)


class IconSettingBuilder(ModelBuilder[IconSetting]):

    def __init__(self, icon_builder: LibraryIconFileBuilder = LibraryIconFileBuilder(),
                 config_builder: RuleManagerBuilder = RuleManagerBuilder()) -> None:
        super().__init__()
        self.icon_builder = icon_builder
        self.config_builder = config_builder
        self.rule_configs: Dict[str, RuleManager] = {}

    def update_rules(self, rules: Iterable[File]):
        rule_configs = self.config_builder.build_models(rules)
        for rule in rule_configs:
            self.rule_configs[rule.name] = rule

    def build_icons(self, files: Iterable[File]) -> List[LibraryIconFile]:
        return self.icon_builder.build_models(files)

    def get_rule_manager(self, model: LibraryIconFile) -> Optional[RuleManager]:
        return self.rule_configs.get(model.name_wo_extension, None)

    def can_build(self, model: PathModel) -> bool:
        if not isinstance(model, LibraryIconFile):
            return False
        config = self.get_rule_manager(model)
        return config is not None

    def build_model(self, file: LibraryIconFile) -> Optional[IconSetting]:
        config = self.get_rule_manager(file)
        if config is None:
            return None
        return IconSetting(file, config)

    def update_config(self, setting: IconSetting, template_file: JsonFile) -> None:
        config = setting.manager.config
        self.config_builder.factory.update(config, template_file)


class ISettingsController(ILibraryController):

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        ...

    def create_icon_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        ...

    def setting_by_icon(self, icon: IconFile) -> Optional[IconSetting]:
        ...

    def create_settings(self, content: Dict[str, List[File]]):
        ...

    def create_icon_configs(self):
        ...

    def update_icon_configs(self):
        ...

    def delete_icon_configs(self):
        ...

    def archive_library(self):
        ...


class IconSettingController(ISettingsController):

    icons_extensions = [
        IconFile.extension(with_point=False),
        JsonFile.extension(with_point=False)
    ]

    def __init__(self, builder: IconSettingBuilder = IconSettingBuilder()) -> None:
        self.builder = builder
        self.library_icons: Iterable[LibraryIconFile] = []
        self._settings: List[IconSetting] = []

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        if clean_empty:
            return list(filter(lambda ico: not ico.is_empty(), self._settings))
        return self._settings

    def create_icon_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        # settings = copy.deepcopy(self.settings(clean_empty=True))
        settings = self.settings(clean_empty=True)
        for setting in settings:
            setting.set_before_or_after(before_or_after)
        return settings

    def create_settings(self, content: Dict[str, List[File]]):
        rules = content.get(JsonFile.extension(with_point=False), [])
        self.builder.update_rules(rules=rules)
        icons = content.get(LibraryIconFile.extension(with_point=False), [])
        self.library_icons = self.builder.build_icons(icons)
        self._settings = self.builder.build_models(self.library_icons)
        self.clean_empty_rules()
        self._settings.sort(key=lambda ele: ele.order_key)

    def clean_empty_rules(self):
        for setting in self._settings:
            setting.manager.clean_empty()

    def create_icon_configs(self):
        template = icon_setting_template()
        for icon_file in self.library_icons:
            icon_config = icon_file.get_config()
            if icon_config.exists():
                continue
            template.copy_to(icon_config)
            log.info(f'Created template for {icon_file.name_wo_extension}')

    def update_icon_configs(self):
        template = icon_setting_template()
        for setting in self._settings:
            self.builder.update_config(setting, template)

    def delete_icon_configs(self):
        configs = [setting.manager.config for setting in self._settings]
        action = DeleteAction(configs)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(RuleManager))

    def archive_library(self):
        for setting in self._settings:
            if not setting.is_empty():
                continue
            archive_files = setting.archive_files()
            for file in archive_files:
                self.archive_file(file)
            log.info(f'Archive {len(archive_files)} of {setting.name}')

    def archive_file(self, file: FileModel):
        folder = self.get_archive_folder(file)
        archive = folder.get_archive_file(file)
        file.copy_to(archive)
        file.remove()

    def get_archive_folder(self, icon: FileModel):
        folder_path = ArchiveFolder.get_folder_path(icon)
        folder = ArchiveFolder(folder_path)
        if not folder.exists():
            folder.create()
        return folder

    def setting_by_icon(self, icon: IconFile) -> Optional[IconSetting]:
        for setting in self._settings:
            if setting.icon.name != icon.name:
                continue
            return setting
        return None
