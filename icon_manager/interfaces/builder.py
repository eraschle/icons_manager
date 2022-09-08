import concurrent.futures
from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, Protocol, TypeVar

from icon_manager.helpers.path import File, Folder, Path
from icon_manager.interfaces.path import PathModel

TModel = TypeVar('TModel', bound=object)

TEntry = TypeVar('TEntry', PathModel, Path, contravariant=True)


class Builder(Protocol, Generic[TEntry, TModel]):

    def setup(self, **kwargs) -> None:
        ...

    def build_models(self, entries: Iterable[TEntry], **kwargs) -> List[TModel]:
        ...

    def build_model(self, entry: TEntry, **kwargs) -> Optional[TModel]:
        ...


class CrawlerBuilder(ABC, Builder[Path, TModel]):

    def __init__(self) -> None:
        super().__init__()
        self.models: List[TModel] = []

    def setup(self, **kwargs) -> None:
        pass

    def build_models(self, entries: Iterable[Path], **kwargs) -> List[TModel]:
        models = []
        for entry in entries:
            model = self.build_model(entry, **kwargs)
            if model is None:
                continue
            models.append(model)
            if isinstance(entry, Folder):
                models.extend(self.build_models(entry.files))
                models.extend(self.build_models(entry.folders))
        return models

    def build_models_async(self, entries: Iterable[Path], **kwargs) -> List[TModel]:
        models: List[TModel] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            task = {executor.submit(self.build_models, ele): ele for ele in entries}
            for future in concurrent.futures.as_completed(task):
                entry = task[future]
                try:
                    model = future.result()
                    if model is None:
                        continue
                    models.extend(model)
                except Exception as exc:
                    print('%r Exception: %s' % (entry.path, exc))
        return models

    def build_model(self, entry: Path, **kwargs) -> Optional[TModel]:
        if isinstance(entry, Folder):
            if not self.can_build_folder(entry, **kwargs):
                return None
            return self.build_folder_model(entry, **kwargs)
        if not self.can_build_file(entry, **kwargs):
            return None
        return self.build_file_model(entry, **kwargs)

    @abstractmethod
    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        pass

    @abstractmethod
    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[TModel]:
        pass

    @abstractmethod
    def can_build_file(self, file: File, **kwargs) -> bool:
        pass

    @abstractmethod
    def build_file_model(self, file: File, **kwargs) -> Optional[TModel]:
        pass


class FolderCrawlerBuilder(CrawlerBuilder[TModel]):

    def can_build_file(self, file: File, **kwargs) -> bool:
        return False

    def build_file_model(self, file: File, **kwargs) -> Optional[TModel]:
        return None


class FileCrawlerBuilder(CrawlerBuilder[TModel]):

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return False

    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[TModel]:
        return None


class ModelBuilder(ABC, Builder[PathModel, TModel]):

    def setup(self, **kwargs) -> None:
        pass

    @ abstractmethod
    def can_build(self, entry: PathModel, **kwargs) -> bool:
        ...

    def build_models(self, entries: Iterable[PathModel], **kwargs) -> List[TModel]:
        models: List[TModel] = []
        for entry in entries:
            if not self.can_build(entry):
                continue
            model = self.build_model(entry, **kwargs)
            if model is None:
                continue
            models.append(model, **kwargs)
        return models

    @ abstractmethod
    def build_model(self, entry: PathModel, **kwargs) -> Optional[TModel]:
        ...
