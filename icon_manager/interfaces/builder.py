from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, Protocol, TypeVar

from icon_manager.interfaces.path import File, Folder, Node, PathModel

TModel = TypeVar("TModel", bound=object)

TEntry = TypeVar("TEntry", PathModel, Node, contravariant=True)


class Builder(Protocol, Generic[TEntry, TModel]):  # noqa: UP046 - TEntry is constrained and contravariant
    """Turns crawled entries into models.

    There used to be a setup(**kwargs) here, through which the builders that
    need the icon settings received them before build_models was called.
    That made every builder's state mutable between construction and use -
    which is how one user configuration ended up matching against another's
    settings - and it put untyped **kwargs on all eight hooks below, where
    no implementation ever read them. A builder that needs data takes it in
    its constructor.
    """

    def build_models(self, nodes: Iterable[TEntry]) -> list[TModel]: ...

    def build_model(self, node: TEntry) -> TModel | None: ...


class CrawlerBuilder(ABC, Builder[Node, TModel]):
    def build_models(self, nodes: Iterable[Node]) -> list[TModel]:
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
            model = self.build_model(entry)
            if model is not None:
                models.append(model)
            if isinstance(entry, Folder):
                models.extend(self.build_models(entry.files))
                models.extend(self.build_models(entry.folders))
        return models

    def build_model(self, node: Node) -> TModel | None:
        """Dispatch to the folder or the file hooks.

        Decided by the node's type, not by ``is_dir()``: the crawler already
        knows which it built, so asking the filesystem again was a stat call
        per node, and it answered wrong for an entry deleted since the crawl.
        """
        if isinstance(node, Folder):
            if not self.can_build_folder(node):
                return None
            return self.build_folder_model(node)
        if not isinstance(node, File):
            return None
        if not self.can_build_file(node):
            return None
        return self.build_file_model(node)

    @abstractmethod
    def can_build_folder(self, folder: Folder) -> bool:
        """Whether ``folder`` should become a model."""

    @abstractmethod
    def build_folder_model(self, folder: Folder) -> TModel | None:
        """The model for ``folder``, or None."""

    @abstractmethod
    def can_build_file(self, file: File) -> bool:
        """Whether ``file`` should become a model."""

    @abstractmethod
    def build_file_model(self, file: File) -> TModel | None:
        """The model for ``file``, or None."""


class FolderCrawlerBuilder(CrawlerBuilder[TModel]):
    """A builder that only ever produces models for folders."""

    def can_build_file(self, file: File) -> bool:
        return False

    def build_file_model(self, file: File) -> TModel | None:
        return None


class FileCrawlerBuilder(CrawlerBuilder[TModel]):
    """A builder that only ever produces models for files."""

    def can_build_folder(self, folder: Folder) -> bool:
        return False

    def build_folder_model(self, folder: Folder) -> TModel | None:
        return None


class ModelBuilder(ABC, Builder[PathModel, TModel]):
    """Builds models from path models rather than from a crawl result."""

    @abstractmethod
    def can_build(self, entry: PathModel) -> bool: ...

    @abstractmethod
    def build_model(self, node: PathModel) -> TModel | None: ...

    def build_models(self, nodes: Iterable[PathModel]) -> list[TModel]:
        models: list[TModel] = []
        for entry in nodes:
            if not self.can_build(entry):
                continue
            model = self.build_model(entry)
            if model is not None:
                models.append(model)
        return models
