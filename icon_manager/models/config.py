import os
from typing import Collection, Tuple

from icon_manager.models.path import FolderModel, IconFile, JsonFile
from icon_manager.models.rules import FilterRuleManager, Operator


class IconConfig:
    def __init__(self, icon_file: IconFile,
                 managers: Collection[FilterRuleManager],
                 operator: Operator,
                 copy_icon: bool,
                 weight: int) -> None:
        self.icon_file = icon_file
        self.copy_icon = copy_icon
        self.managers = managers
        self.operator = operator
        self.order_weight = weight

    def config_file(self) -> JsonFile:
        folder = os.path.dirname(self.icon_file.path)
        name = self.icon_file.name_wo_extension
        file_name = f'{name}.{JsonFile.extension()}'
        file_path = os.path.join(folder, file_name)
        return JsonFile(file_path)

    def order_key(self) -> Tuple[str, str]:
        weight = f'{self.order_weight:02d}'
        return (weight, self.icon_file.name_wo_extension)

    def is_empty(self) -> bool:
        if len(self.managers) == 0:
            return True
        return all(manager.is_empty() for manager in self.managers)

    def is_config_for(self, folder: FolderModel) -> bool:
        if self.operator == Operator.ALL:
            return all(manager.is_allowed(folder) for manager in self.managers)
        return any(manager.is_allowed(folder) for manager in self.managers)

    def __str__(self) -> str:
        return f'Config: {self.icon_file.name_wo_extension}'

    def __repr__(self) -> str:
        output = self.__str__()
        for manager in self.managers:
            output = f'{output} {manager.attribute} [{manager.rule_count()}]'
        return output
