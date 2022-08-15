from typing import Iterable

from icon_manager.source.base import Source
from icon_manager.models.path import DesktopIniFile


class DesktopFileSource(Source[DesktopIniFile, Iterable[str]]):

    def read(self, source: DesktopIniFile) -> Iterable[str]:
        content = []
        with open(source.path, mode='r') as file:
            content = file.readlines()
            file.close()
        return content

    def write(self, source: DesktopIniFile, content: Iterable[str]) -> None:
        content_to_write = '\n'.join(content)
        with open(source.path, 'w') as file:
            file.write(content_to_write)
            file.close()
