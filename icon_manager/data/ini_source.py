from collections.abc import Iterable

from icon_manager.content.models.desktop import DesktopIniFile
from icon_manager.data.base import Source


class DesktopFileSource(Source[DesktopIniFile, Iterable[str]]):
    def read(self, source: DesktopIniFile) -> Iterable[str]:
        content = []
        with open(source.path) as file:
            content = file.readlines()
            file.close()
        return content

    def write(self, source: DesktopIniFile, content: Iterable[str]) -> None:
        content_to_write = "\n".join(content)
        with open(source.path, "w") as file:
            file.write(content_to_write)
            file.close()
