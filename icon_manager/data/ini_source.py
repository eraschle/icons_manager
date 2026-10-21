from collections.abc import Iterable

from icon_manager.data.base import Source
from icon_manager.interfaces.path import FileModel


class TextLineSource(Source[FileModel, Iterable[str]]):
    """Reads and writes a text file as a sequence of lines.

    Typed to FileModel rather than DesktopIniFile: nothing here is specific
    to desktop.ini, and importing that type made the data layer depend on
    the content layer above it.

    UTF-8 explicitly, in both directions. Reading used the platform's locale
    encoding before, which decodes the same desktop.ini differently on two
    machines. Lines are returned without their terminator and written with
    one each, so a file survives a read/write round trip unchanged - read
    kept the newlines while write re-joined them, which appended a blank
    line on every rewrite.
    """

    def read(self, source: FileModel) -> Iterable[str]:
        with open(source.path, encoding="utf-8") as file:
            return file.read().splitlines()

    def write(self, source: FileModel, content: Iterable[str]) -> None:
        with open(source.path, mode="w", encoding="utf-8") as file:
            file.writelines(f"{line}\n" for line in content)
