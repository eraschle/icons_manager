import logging
from collections.abc import Iterable, Sequence

from icon_manager.content.models.matched import IconSetting
from icon_manager.helpers.resource import icon_setting_template
from icon_manager.interfaces.actions import DeleteAction
from icon_manager.interfaces.builder import FileCrawlerBuilder, ModelBuilder
from icon_manager.interfaces.controller import IConfigHandler, ISettingsHandler
from icon_manager.interfaces.path import File, FileModel, JsonFile, PathModel
from icon_manager.library.models import ArchiveFolder, IconFile, LibraryIconFile
from icon_manager.rules.factory.manager import RuleManagerFactory
from icon_manager.rules.manager import RuleManager

log = logging.getLogger(__name__)


class RuleManagerBuilder(FileCrawlerBuilder[RuleManager]):
    """Builder for creating RuleManager instances from files."""

    def __init__(self, factory: RuleManagerFactory = RuleManagerFactory()) -> None:
        """Initialize RuleManagerBuilder with a factory.

        Args:
            factory: Factory for creating RuleManager instances.
        """
        self.factory = factory

    def can_build_file(self, file: File, **kwargs) -> bool:
        """Check if file can be built into a RuleManager.

        Args:
            file: File to check.
            **kwargs: Additional arguments.

        Returns:
            True if file is a JSON file, False otherwise.
        """
        return JsonFile.is_model(file.path)

    def build_file_model(self, file: File, **kwargs) -> RuleManager | None:
        """Build a RuleManager from a file.

        Args:
            file: File to build from.
            **kwargs: Additional arguments.

        Returns:
            RuleManager instance or None if creation fails.
        """
        return self.factory.create(JsonFile(file.path))


class LibraryIconFileBuilder(FileCrawlerBuilder[LibraryIconFile]):
    """Builder for creating LibraryIconFile instances from files."""

    def can_build_file(self, file: File, **kwargs) -> bool:
        """Check if file can be built into a LibraryIconFile.

        Args:
            file: File to check.
            **kwargs: Additional arguments.

        Returns:
            True if file is a valid icon file, False otherwise.
        """
        return LibraryIconFile.is_model(file.name)

    def build_file_model(self, file: File, **kwargs) -> LibraryIconFile | None:
        """Build a LibraryIconFile from a file.

        Args:
            file: File to build from.
            **kwargs: Additional arguments.

        Returns:
            LibraryIconFile instance or None if creation fails.
        """
        return LibraryIconFile(file.path)


class IconSettingBuilder(ModelBuilder[IconSetting]):
    """Builder for creating IconSetting instances from LibraryIconFile instances."""

    def __init__(
        self,
        icon_builder: LibraryIconFileBuilder = LibraryIconFileBuilder(),
        config_builder: RuleManagerBuilder = RuleManagerBuilder(),
    ) -> None:
        """Initialize IconSettingBuilder with builders for icons and configurations.

        Args:
            icon_builder: Builder for creating LibraryIconFile instances.
            config_builder: Builder for creating RuleManager instances.
        """
        super().__init__()
        self.icon_builder = icon_builder
        self.config_builder = config_builder
        self.rule_configs: dict[str, RuleManager] = {}

    def update_rules(self, rules: Iterable[File]):
        """Update rule configurations from rule files.

        Args:
            rules: Iterable of rule files to process.
        """
        rule_configs = self.config_builder.build_models(rules)
        for rule in rule_configs:
            self.rule_configs[rule.name] = rule

    def build_icons(self, files: Iterable[File]) -> list[LibraryIconFile]:
        """Build LibraryIconFile instances from icon files.

        Args:
            files: Iterable of icon files to build.

        Returns:
            List of LibraryIconFile instances.
        """
        return self.icon_builder.build_models(files)

    def get_rule_manager(self, model: LibraryIconFile) -> RuleManager | None:
        """Get rule manager for a library icon file.

        Args:
            model: LibraryIconFile to get rule manager for.

        Returns:
            RuleManager instance or None if not found.
        """
        return self.rule_configs.get(model.name_wo_extension, None)

    def can_build(self, model: PathModel) -> bool:
        """Check if model can be built into an IconSetting.

        Args:
            model: PathModel to check.

        Returns:
            True if model is a LibraryIconFile with associated config, False otherwise.
        """
        if not isinstance(model, LibraryIconFile):
            return False
        config = self.get_rule_manager(model)
        return config is not None

    def build_model(self, file: LibraryIconFile) -> IconSetting | None:
        """Build an IconSetting from a LibraryIconFile.

        Args:
            file: LibraryIconFile to build from.

        Returns:
            IconSetting instance or None if no config found.
        """
        config = self.get_rule_manager(file)
        if config is None:
            return None
        return IconSetting(file, config)

    def update_config(self, setting: IconSetting, template_file: JsonFile) -> None:
        """Update configuration for an icon setting.

        Args:
            setting: IconSetting to update.
            template_file: Template file to use for updates.
        """
        config = setting.manager.config
        self.config_builder.factory.update(config, template_file)


class IconLibraryController(IConfigHandler, ISettingsHandler):
    """Controller for managing icon library operations.

    This controller handles the creation, management, and archiving of icon settings,
    including their associated configuration files and rule management.
    """

    icons_extensions = [
        IconFile.extension(with_point=False),
        JsonFile.extension(with_point=False),
    ]

    def __init__(self, builder: IconSettingBuilder = IconSettingBuilder()) -> None:
        """Initialize IconLibraryController with a builder.

        Args:
            builder: Builder for creating IconSetting instances.
        """
        self.builder = builder
        self.library_icons: Iterable[LibraryIconFile] = []
        self._settings: list[IconSetting] = []

    def settings(self, clean_empty: bool = True) -> Sequence[IconSetting]:
        """Get icon settings with optional filtering.

        Args:
            clean_empty: Whether to filter out empty settings.

        Returns:
            Sequence of IconSetting instances.
        """
        if clean_empty:
            return list(filter(lambda ico: not ico.is_empty(), self._settings))
        return self._settings

    def create_icon_settings(self, before_or_after: Iterable[str]) -> Sequence[IconSetting]:
        """Create icon settings with before/after configuration.

        Args:
            before_or_after: Iterable of before/after settings.

        Returns:
            Sequence of configured IconSetting instances.
        """
        # settings = copy.deepcopy(self.settings(clean_empty=True))
        settings = self.settings(clean_empty=True)
        for setting in settings:
            setting.set_before_or_after(before_or_after)
        return settings

    def create_settings(self, content: dict[str, list[File]]):
        """Create settings from content dictionary.

        Args:
            content: Dictionary mapping file extensions to file lists.
        """
        rules = content.get(JsonFile.extension(with_point=False), [])
        self.builder.update_rules(rules=rules)
        icons = content.get(LibraryIconFile.extension(with_point=False), [])
        self.library_icons = self.builder.build_icons(icons)
        self._settings = self.builder.build_models(self.library_icons)
        self.clean_empty_rules()
        self._settings.sort(key=lambda ele: ele.order_key)

    def clean_empty_rules(self):
        """Clean empty rules from all settings."""
        for setting in self._settings:
            setting.manager.clean_empty()

    def create_icon_configs(self):
        """Create configuration files for icons that don't have them."""
        template = icon_setting_template()
        for icon_file in self.library_icons:
            icon_config = icon_file.get_config()
            if icon_config.exists():
                continue
            template.copy_to(icon_config)
            log.info(f"Created template for {icon_file.name_wo_extension}")

    def update_icon_configs(self):
        """Update all icon configuration files with template data."""
        template = icon_setting_template()
        for setting in self._settings:
            self.builder.update_config(setting, template)

    def delete_icon_configs(self):
        """Delete all icon configuration files."""
        configs = [setting.manager.config for setting in self._settings]
        action = DeleteAction(configs)
        action.execute()
        if not action.any_executed():
            return
        log.info(action.get_log_message(RuleManager))

    def archive_library(self):
        """Archive empty settings in the library."""
        for setting in self._settings:
            if not setting.is_empty():
                continue
            archive_files = setting.archive_files()
            for file in archive_files:
                self.archive_file(file)
            log.info(f"Archive {len(archive_files)} of {setting.name}")

    def archive_file(self, file: FileModel):
        """Archive a single file.

        Args:
            file: File to archive.
        """
        folder = self.get_archive_folder(file)
        archive = folder.get_archive_file(file)
        file.copy_to(archive)
        file.remove()

    def get_archive_folder(self, icon: FileModel):
        """Get or create archive folder for an icon.

        Args:
            icon: Icon file to get archive folder for.

        Returns:
            ArchiveFolder instance.
        """
        folder_path = ArchiveFolder.get_folder_path(icon)
        folder = ArchiveFolder(folder_path)
        if not folder.exists():
            folder.create()
        return folder

    def setting_by_icon(self, icon: IconFile) -> IconSetting | None:
        """Find setting by icon file.

        Args:
            icon: Icon file to find setting for.

        Returns:
            IconSetting instance or None if not found.
        """
        for setting in self._settings:
            if setting.icon.name != icon.name:
                continue
            return setting
        return None
