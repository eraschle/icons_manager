from typing import Iterable, Tuple

from icon_manager.models.path import FolderModel, IconFile
from icon_manager.models.rules import FilterRuleManager


class IconConfig:
    def __init__(self, icon_file: IconFile,
                 managers: Iterable[FilterRuleManager],
                 weight: int) -> None:
        self.icon_file = icon_file
        self.managers = managers
        self.order_weight = weight

    def order_key(self) -> Tuple[str, str]:
        weight = f'{self.order_weight:02d}'
        return (weight, self.icon_file.name_wo_extension)

    def is_empty(self) -> bool:
        return all(manager.is_empty() for manager in self.managers)

    def is_config_for(self, folder: FolderModel) -> bool:
        return all(manager.is_allowed(folder) for manager in self.managers)

    def __str__(self) -> str:
        return f'Config: {self.icon_file.name_wo_extension}'

    def __repr__(self) -> str:
        output = self.__str__()
        for manager in self.managers:
            output = f'{output} {manager.attribute} [{manager.rule_count()}]'
        return output
