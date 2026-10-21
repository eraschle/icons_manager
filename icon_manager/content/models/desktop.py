from icon_manager.interfaces.path import FileModel

GIT_FOLDER_NAME = ".git"


def is_git_folder(path: str) -> bool:
    """Whether ``path`` is a repository's .git folder.

    Was a FileModel subclass that was never instantiated, had no extension
    to report and described a folder - a predicate in class clothing.
    """
    return path.endswith(GIT_FOLDER_NAME)


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
