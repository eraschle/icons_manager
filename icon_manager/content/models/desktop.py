from icon_manager.interfaces.path import FileModel


class Git(FileModel):
    file_name = ".git"

    @classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.file_name)


class DesktopIniFile(FileModel):
    file_name = "desktop.ini"

    @classmethod
    def is_model(cls, path: str) -> bool:
        return path.endswith(cls.file_name)

    @classmethod
    def _extension(cls) -> str:
        return "ini"

    def set_protected_and_hidden(self) -> None:
        self.set_attrib({"s": "+", "h": "+"})

    def set_writeable_and_visible(self) -> None:
        self.set_attrib({"s": "-", "h": "-"})
