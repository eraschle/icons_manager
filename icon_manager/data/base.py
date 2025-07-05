from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from icon_manager.interfaces.path import FileModel

TSource = TypeVar("TSource", bound=FileModel)
TContent = TypeVar("TContent", bound=object)


class Source(ABC, Generic[TSource, TContent]):
    @abstractmethod
    def read(self, source: TSource) -> TContent: ...

    @abstractmethod
    def write(self, source: TSource, content: TContent): ...
