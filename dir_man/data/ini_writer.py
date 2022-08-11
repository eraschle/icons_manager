from typing import Iterable

from dir_man.models.container import ConfiguredContainer


class DesktopFileWriter:

    def get_ini_lines(self, container: ConfiguredContainer) -> Iterable[str]:
        icon_path = container.config_icon_path()
        return [
            '[.ShellClassInfo]',
            f'IconResource={icon_path},0',
            '[ViewState]',
            'Mode=',
            'Vid=',
            'FolderType=Generic'
        ]

    def get_ini_content(self, container: ConfiguredContainer) -> str:
        content_lines = self.get_ini_lines(container)
        return '\n'.join(content_lines)

    def write_file(self, container: ConfiguredContainer) -> None:
        ini_path = container.ini_file
        with open(ini_path.path, 'w') as file:
            content = self.get_ini_content(container)
            file.write(content)
            file.close()

    def write_config(self, container: ConfiguredContainer) -> ConfiguredContainer:
        try:
            self.write_file(container)
        except Exception as ex:
            container.add_error('Write file', ex)
        return container
