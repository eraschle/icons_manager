from icon_manager.rules.manager import ExcludeManager


class FilterOptions:
    def __init__(
        self,
        exclude: ExcludeManager,
        clean_excluded: bool,
        clean_project: bool,
        clean_recursive: bool,
    ) -> None:
        self.clean_excluded = clean_excluded
        self.clean_project = clean_project
        self.clean_recursive = clean_recursive
        self.exclude = exclude
