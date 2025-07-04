from typing import Generic, Protocol, TypeVar

from icon_manager.interfaces.path import FileModel

TContent = TypeVar("TContent", contravariant=True)
TModel = TypeVar("TModel", bound=object, covariant=True)


class ContentFactory(Protocol, Generic[TContent, TModel]):
    def create(self, rule_config: TContent, **kwargs) -> TModel: ...


TFile = TypeVar("TFile", bound=FileModel, contravariant=True)


class FileFactory(Protocol, Generic[TFile, TModel]):
    def create(self, file: TFile, **kwargs) -> TModel: ...
