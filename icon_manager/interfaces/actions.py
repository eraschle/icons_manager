import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Generic, List, Optional, Sequence, TypeVar

from icon_manager.config.user import UserConfig
from icon_manager.helpers.string import (ALIGN_LEFT, ALIGN_RIGHT, THOUSAND,
                                         fixed_length, list_value,
                                         prefix_value,)
from icon_manager.interfaces.path import PathModel

log = logging.getLogger(__name__)


TEntry = TypeVar("TEntry", bound=PathModel)


class Action(ABC, Generic[TEntry]):
    """Abstract base class for path operations.

    This class provides a framework for executing actions on collections of
    path entries (files and folders). Subclasses must implement the specific
    action logic and conditions for execution.

    Type Parameters:
        TEntry: Type of path entries this action operates on, must be bound to PathModel.
    """

    def __init__(self, config: Optional[UserConfig], entries: Sequence[TEntry], action_log: str) -> None:
        super().__init__()
        self.config = config
        self.entries = entries
        self.files: list[PathModel] = []
        self.folders: list[PathModel] = []
        self._action_log = action_log
        self._lock = Lock()

    def execute(self) -> None:
        """Execute the action on all entries that meet the execution criteria.

        This method iterates through all entries, checks if each can be executed,
        categorizes them as files or folders, and executes the specific action.
        """
        for entry in self.entries:
            self.action_execute(entry)

    def async_execute(self) -> None:
        prefix = 'execute action'
        if self.config is not None:
            prefix = f'execute action {self.config.name}'
        with ThreadPoolExecutor(thread_name_prefix=prefix,
                                max_workers=len(self.entries)) as executor:
            task = {executor.submit(
                self.action_execute, entry): entry for entry in self.entries}
            for future in as_completed(task):
                setting = task[future]
                try:
                    future.result()
                except Exception as exc:
                    log.exception("%r Exception: %s" % (setting, exc))

    def action_execute(self, entry: TEntry) -> None:
        if not self.can_execute(entry):
            return
        if entry.is_file():
            self.files.append(entry)
        if entry.is_dir():
            self.folders.append(entry)
        self.execute_action(entry)

    @abstractmethod
    def can_execute(self, entry: TEntry) -> bool:
        """Check if the action can be executed on the given entry.

        Parameters
        ----------
        entry : TEntry
            Path entry to check.

        Returns
        -------
        bool
            True if the action can be executed on this entry, False otherwise.
        """
        pass

    @abstractmethod
    def execute_action(self, entry: TEntry) -> None:
        """Execute the specific action on the given entry.

        Parameters
        ----------
        entry : TEntry
            Path entry to execute the action on.

        Notes
        -----
        This method is called for each entry that passes the can_execute check.
        """
        pass

    def any_executed(self) -> bool:
        """Check if any actions were executed.

        Returns
        -------
        bool
            True if at least one file or folder was processed, False otherwise.
        """
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
        """Generate complete log message for the action.

        Parameters
        ----------
        model : type
            Model class to include in the log message.

        Returns
        -------
        str
            Complete formatted log message including action, files, and folders.
        """
        name = self._log_prefix(model)
        action = self._log_action()
        files = self._log_files()
        folders = self._log_folders()
        return f'{name}: {action} "{files}" Files / "{folders}" Folders'


class DeleteAction(Action[PathModel]):
    """Concrete action implementation for deleting path entries.

    This action removes files and folders from the filesystem. It only operates
    on entries that exist on the filesystem.
    """

    def __init__(self, config: Optional[UserConfig], entries: Sequence[PathModel]) -> None:
        super().__init__(config, entries, 'Deleted')

    def can_execute(self, entry: PathModel) -> bool:
        """Check if entry can be deleted.

        Parameters
        ----------
        entry : PathModel
            Path entry to check.

        Returns
        -------
        bool
            True if the entry exists on the filesystem, False otherwise.
        """
        return entry.exists()

    def execute_action(self, entry: PathModel) -> None:
        """Delete the specified entry from the filesystem.

        Parameters
        ----------
        entry : PathModel
            Path entry to delete.
        """
        entry.remove()
