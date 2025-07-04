from typing import Protocol, TypeVar

from icon_manager.interfaces.path import FileModel

TContent = TypeVar("TContent", contravariant=True)
TModel = TypeVar("TModel", bound=object, covariant=True)


class ContentFactory(Protocol[TContent, TModel]):
    def create(self, config: TContent, **kwargs) -> TModel: ...


TFile = TypeVar("TFile", bound=FileModel, contravariant=True)


class FileFactory(Protocol[TFile, TModel]):
    def create(self, file: TFile, **kwargs) -> TModel: ...
