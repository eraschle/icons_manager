from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, Protocol, TypeVar

from icon_manager.interfaces.path import Folder, Node
from icon_manager.interfaces.path import PathModel

TModel = TypeVar('TModel', bound=object)

TEntry = TypeVar('TEntry', PathModel, Node, contravariant=True)


class Builder(Protocol, Generic[TEntry, TModel]):

    def setup(self, **kwargs) -> None:
        ...

    def build_models(self, nodes: Iterable[TEntry], **kwargs) -> List[TModel]:
        ...

    def build_model(self, node: TEntry, **kwargs) -> Optional[TModel]:
        ...


class CrawlerBuilder(ABC, Builder[Node, TModel]):

    def __init__(self) -> None:
        super().__init__()
        self.models: List[TModel] = []

    def setup(self, **kwargs) -> None:
        pass

    def build_models(self, nodes: Iterable[Node], **kwargs) -> List[TModel]:
        models = []
        for entry in nodes:
            if entry.excluded:
                continue
            model = self.build_model(entry, **kwargs)
            if model is None:
                continue
            models.append(model)
            if isinstance(entry, Folder):
                models.extend(self.build_models(entry.files))
                models.extend(self.build_models(entry.folders))
        return models

    # def build_models_async(self, nodes: Iterable[Node], **kwargs) -> List[TModel]:
    #     models: List[TModel] = []
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         task = {executor.submit(self.build_models, node): node for node in nodes}
    #         for future in concurrent.futures.as_completed(task):
    #             entry = task[future]
    #             try:
    #                 model = future.result()
    #                 if model is None:
    #                     continue
    #                 models.extend(model)
    #             except Exception as exc:
    #                 print('%r Exception: %s' % (entry.path, exc))
    #     return models

    def build_model(self, node: Node, **kwargs) -> Optional[TModel]:
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
    def build_folder_model(self, folder: Node, **kwargs) -> Optional[TModel]:
        pass

    @abstractmethod
    def can_build_file(self, file: Node, **kwargs) -> bool:
        pass

    @abstractmethod
    def build_file_model(self, file: Node, **kwargs) -> Optional[TModel]:
        pass


class FolderCrawlerBuilder(CrawlerBuilder[TModel]):

    def can_build_file(self, file: Node, **kwargs) -> bool:
        return False

    def build_file_model(self, file: Node, **kwargs) -> Optional[TModel]:
        return None


class FileCrawlerBuilder(CrawlerBuilder[TModel]):

    def can_build_folder(self, folder: Node, **kwargs) -> bool:
        return False

    def build_folder_model(self, folder: Node, **kwargs) -> Optional[TModel]:
        return None


class ModelBuilder(ABC, Builder[PathModel, TModel]):

    def setup(self, **kwargs) -> None:
        pass

    @ abstractmethod
    def can_build(self, entry: PathModel, **kwargs) -> bool:
        ...

    def build_models(self, nodes: Iterable[PathModel], **kwargs) -> List[TModel]:
        models: List[TModel] = []
        for entry in nodes:
            if not self.can_build(entry):
                continue
            model = self.build_model(entry, **kwargs)
            if model is None:
                continue
            models.append(model, **kwargs)
        return models

    @ abstractmethod
    def build_model(self, node: PathModel, **kwargs) -> Optional[TModel]:
        ...
