import logging
from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, TypeVar

from icon_manager.helpers.string import (ALIGN_LEFT, ALIGN_RIGHT, THOUSAND,
                                         fixed_length, list_value,
                                         prefix_value)
from icon_manager.interfaces.path import PathModel

log = logging.getLogger(__name__)


TEntry = TypeVar('TEntry', bound=PathModel)


class Action(ABC, Generic[TEntry]):

    def __init__(self, entries: Iterable[TEntry], action_log: str) -> None:
        super().__init__()
        self.entries = entries
        self.files: List[PathModel] = []
        self.folders: List[PathModel] = []
        self._action_log = action_log

    def execute(self) -> None:
        for entry in self.entries:
            if not self.can_execute(entry):
                continue
            if entry.is_file():
                self.files.append(entry)
            if entry.is_dir():
                self.folders.append(entry)
            self.execute_action(entry)

    @abstractmethod
    def can_execute(self, entry: TEntry) -> bool:
        pass

    @abstractmethod
    def execute_action(self, entry: TEntry) -> None:
        pass

    def any_executed(self) -> bool:
        return len(self.files) > 0 or len(self.folders) > 0

    def _log_prefix(self, model: type, width: int = 10, align: str = ALIGN_LEFT) -> str:
        return prefix_value(model.__name__, width=width, align=align)

    def _log_action(self, width: int = 20, align: str = ALIGN_LEFT) -> str:
        return fixed_length(self._action_log, width=width, align=align)

    def _log_files(self, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
        return list_value(self.files, width=width, align=align)

    def _log_folders(self, width: int = THOUSAND, align: str = ALIGN_RIGHT) -> str:
        return list_value(self.folders, width=width, align=align)

    def get_log_message(self, model: type) -> str:
        name = self._log_prefix(model)
        action = self._log_action()
        files = self._log_files()
        folders = self._log_folders()
        return f'{name}: {action} "{files}" Files / "{folders}" Folders'


class DeleteAction(Action[PathModel]):

    def __init__(self, entries: Iterable[PathModel]) -> None:
        super().__init__(entries, 'Deleted')

    def can_execute(self, entry: PathModel) -> bool:
        return entry.exists()

    def execute_action(self, entry: PathModel) -> None:
        entry.remove()
