from typing import Collection, Tuple

from icon_manager.models.path import FolderModel, IconFile
from icon_manager.models.rules import FilterRule


class IconConfig:
    def __init__(self, name: str, icon: IconFile, rules: Collection[FilterRule],
                 apply_to_root: bool, order_weight: int) -> None:
        self.name = name
        self.icon = icon
        self.rules = rules
        self.apply_to_root = apply_to_root
        self.order_weight = order_weight

    def order_key(self) -> Tuple[str, str]:
        weight = f'{self.order_weight:02d}'
        return (weight, self.name)

    def is_config_for(self, folder: FolderModel, is_root_folder: bool) -> bool:
        if not self.apply_to_root and is_root_folder:
            return False
        return all(rule.is_allowed(folder) for rule in self.rules)

    def __str__(self) -> str:
        return f'Config: {self.name}'

    def __repr__(self) -> str:
        return f'{self.__str__()} [Rules: {len(self.rules)}]'
