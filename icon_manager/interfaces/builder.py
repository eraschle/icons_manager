from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, Protocol, TypeVar

from icon_manager.interfaces.path import Folder, Node, PathModel

TModel = TypeVar("TModel", bound=object)

TEntry = TypeVar("TEntry", PathModel, Node, contravariant=True)


class Builder(Protocol, Generic[TEntry, TModel]):  # noqa: UP046 - TEntry is constrained and contravariant
    def setup(self, **kwargs) -> None: ...

    def build_models(self, nodes: Iterable[TEntry], **kwargs) -> list[TModel]: ...

    def build_model(self, node: TEntry, **kwargs) -> TModel | None: ...


class CrawlerBuilder(ABC, Builder[Node, TModel]):
    def __init__(self) -> None:
        super().__init__()
        self.models: list[TModel] = []

    def setup(self, **kwargs) -> None:
        pass

    def build_models(self, nodes: Iterable[Node], **kwargs) -> list[TModel]:
        """Build a model for every node below ``nodes`` that yields one.

        Descending does not depend on the current node yielding a model: the
        recursion used to sit behind ``if model is None: continue``, so a
        search folder - which never matches an icon rule itself - stopped the
        walk at the top level and no nested folder was ever matched.
        """
        models: list[TModel] = []
        for entry in nodes:
            if entry.excluded:
                continue
            model = self.build_model(entry, **kwargs)
            if model is not None:
                models.append(model)
            if isinstance(entry, Folder):
                models.extend(self.build_models(entry.files, **kwargs))
                models.extend(self.build_models(entry.folders, **kwargs))
        return models

    def build_model(self, node: Node, **kwargs) -> TModel | None:
        if node.is_dir():
            if not self.can_build_folder(node, **kwargs):
                return None
            return self.build_folder_model(node, **kwargs)
        if not self.can_build_file(node, **kwargs):
            return None
        return self.build_file_model(node, **kwargs)

    @abstractmethod
    def can_build_folder(self, folder: Node, **kwargs) -> bool:
        pass

    @abstractmethod
    def build_folder_model(self, folder: Node, **kwargs) -> TModel | None:
        pass

    @abstractmethod
    def can_build_file(self, file: Node, **kwargs) -> bool:
        pass

    @abstractmethod
    def build_file_model(self, file: Node, **kwargs) -> TModel | None:
        pass


class FolderCrawlerBuilder(CrawlerBuilder[TModel]):
    def can_build_file(self, file: Node, **kwargs) -> bool:
        return False

    def build_file_model(self, file: Node, **kwargs) -> TModel | None:
        return None


class FileCrawlerBuilder(CrawlerBuilder[TModel]):
    def can_build_folder(self, folder: Node, **kwargs) -> bool:
        return False

    def build_folder_model(self, folder: Node, **kwargs) -> TModel | None:
        return None


class ModelBuilder(ABC, Builder[PathModel, TModel]):
    def setup(self, **kwargs) -> None:
        pass

    @abstractmethod
    def can_build(self, entry: PathModel, **kwargs) -> bool: ...

    def build_models(self, nodes: Iterable[PathModel], **kwargs) -> list[TModel]:
        models: list[TModel] = []
        for entry in nodes:
            if not self.can_build(entry):
                continue
            model = self.build_model(entry, **kwargs)
            if model is None:
                continue
            models.append(model)
        return models

    @abstractmethod
    def build_model(self, node: PathModel, **kwargs) -> TModel | None: ...
