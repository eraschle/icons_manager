from typing import Generic, Protocol, TypeVar

from icon_manager.models.container import ConfiguredContainer

TModel = TypeVar('TModel', contravariant=True)


class PrePostCommand(Protocol, Generic[TModel]):
    def pre_command(self, model: TModel):
        pass

    def post_command(self, model: TModel):
        pass


class ConfigCommand(PrePostCommand[ConfiguredContainer]):

    def pre_command(self, container: ConfiguredContainer):
        pass

    def post_command(self, container: ConfiguredContainer):
        pass


class IconCommand(ConfigCommand):

    def pre_command(self, container: ConfiguredContainer):
        if not container.copy_icon:
            return
        try:
            copied_icon = container.copy_icon_to_local_folder()
            container.config.icon_file = copied_icon
        except Exception as ex:
            container.add_error('copy icon to local', ex)

    def post_command(self, container: ConfiguredContainer):
        if not container.copy_icon:
            return
        try:
            local_folder = container.local_icon_folder()
            local_folder.set_hidden(is_hidden=True)
            # local_folder.set_read_only(is_read_only=True)
            local_icon = container.local_icon_file()
            local_icon.set_hidden(is_hidden=True)
        except Exception as ex:
            container.add_error('set attribute local icon container', ex)


class DesktopAttributeCommand(ConfigCommand):

    def pre_command(self, container: ConfiguredContainer):
        if not container.ini_file.exists():
            return
        try:
            container.ini_file.set_writeable_and_visible()
        except Exception as ex:
            container.add_error('before apply config', ex)

    def post_command(self, container: ConfiguredContainer):
        if not container.ini_file.exists():
            return
        try:
            container.ini_file.set_protected_and_hidden()
            container.set_read_only(is_read_only=True)
        except Exception as ex:
            container.add_error('after apply config', ex)
