from collections.abc import Iterable

from icon_manager.rules.manager import ExcludeManager


class FilterOptions:
    """Which folders the crawler result should drop, and by which names.

    ``excluded_folders`` and ``project_folders`` used to be module globals in
    :mod:`icon_manager.crawler.filters`, assigned by ``UserConfig.validate()``.
    With more than one user configuration the last one assigned won for all of
    them, and since the configurations are crawled concurrently the values
    could even change mid-crawl. They are per-configuration data and travel
    with the options.
    """

    def __init__(
        self,
        exclude: ExcludeManager,
        clean_excluded: bool,
        clean_project: bool,
        clean_recursive: bool,
        excluded_folders: Iterable[str] = (),
        project_folders: Iterable[str] = (),
    ) -> None:
        self.clean_excluded = clean_excluded
        self.clean_project = clean_project
        self.clean_recursive = clean_recursive
        self.exclude = exclude
        self.excluded_folders = frozenset(excluded_folders)
        self.project_folders = frozenset(project_folders)
