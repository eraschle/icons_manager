from collections.abc import Iterable

from icon_manager.rules.manager import ExcludeManager

DEFAULT_PROJECT_DEPTH = 1


class FilterOptions:
    """What the crawler result should drop, and how deep to look.

    All of this is per user configuration. ``skip_names`` and
    ``project_markers`` used to be module globals in
    :mod:`icon_manager.crawler.filters`, assigned by ``UserConfig.validate()``,
    so with more than one configuration the last one assigned won for all of
    them - and since the configurations are crawled concurrently the values
    could change mid-crawl.

    Parameters
    ----------
    exclude
        The sections of ``excluded_rules.config``; each carries whether a
        folder it matches is skipped or becomes a leaf.
    skip_names
        Folder names that never get an icon and are never searched:
        ``exclude_folders`` plus ``code_folders``, since a marker folder
        like ``.git`` is not a folder you give an icon to either.
    project_markers
        Folder names that mark their *parent* as a code project, i.e.
        ``code_folders``. A folder containing one of them is searched
        ``project_depth`` levels deep and no further.
    project_depth
        How far to keep looking inside a project. 1 (the default) offers the
        project's direct children to the rules - so ``myproject/docs`` can
        get an icon - but stops there. 0 makes the project itself a leaf.

        The three booleans that used to be here (``clean_excluded``,
        ``clean_project``, ``clean_recursive``) were never anything but True
        in production, and the only method that read them,
        ``no_filter_options()``, had no caller.
    """

    def __init__(
        self,
        exclude: ExcludeManager,
        skip_names: Iterable[str] = (),
        project_markers: Iterable[str] = (),
        project_depth: int = DEFAULT_PROJECT_DEPTH,
    ) -> None:
        self.exclude = exclude
        self.skip_names = frozenset(skip_names)
        self.project_markers = frozenset(project_markers)
        self.project_depth = max(project_depth, 0)

    def filters_nothing(self) -> bool:
        """Whether these options would leave every crawled folder untouched."""
        return not self.skip_names and not self.project_markers and self.exclude.is_empty()
