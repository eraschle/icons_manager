from abc import ABC, abstractmethod

from icon_manager.interfaces.path import FileModel


class Source[TSource: FileModel, TContent](ABC):
    @abstractmethod
    def read(self, source: TSource) -> TContent: ...

    @abstractmethod
    def write(self, source: TSource, content: TContent): ...
