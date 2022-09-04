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


class CrawlerBuilder(ABC, Builder[Path, TModel]):

    def setup(self, **kwargs) -> None:
        pass

    def create_folder(self, folder: Folder, **kwargs) -> List[TModel]:
        if not self.can_build_folder(folder, **kwargs):
            return []
        model = self.build_folder_model(folder, **kwargs)
        if model is None:
            return []
        return [model]

    def create_file(self, file: File, **kwargs) -> List[TModel]:
        if not self.can_build_file(file, **kwargs):
            return []
        model = self.build_file_model(file, **kwargs)
        if model is None:
            return []
        return [model]

    def create_files(self, files: Iterable[File], **kwargs) -> List[TModel]:
        models = []
        for file in files:
            model = self.create_file(file, **kwargs)
            models.extend(model)
        return models

    def create_models(self, entry: Path, **kwargs) -> List[TModel]:
        if isinstance(entry, Folder):
            models = self.create_folder(entry)
            models.extend(self.create_files(entry.files))
            models.extend(self.build_models(entry.folders))
            return models
        return self.create_file(entry)

    def build_models(self, entries: Iterable[Path], **kwargs) -> List[TModel]:
        models = []
        for entry in entries:
            models.extend(self.create_models(entry))
        return models

    def build_models_async(self, entries: Iterable[Path], **kwargs) -> List[TModel]:
        models: List[TModel] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
            task = {executor.submit(self.create_models, ele): ele for ele in entries}
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

    def can_build_folder(self, folder: Folder, **kwargs) -> bool:
        return False

    def build_folder_model(self, folder: Folder, **kwargs) -> Optional[TModel]:
        return None

    def can_build_file(self, file: File, **kwargs) -> bool:
        return False

    def build_file_model(self, folder: File, **kwargs) -> Optional[TModel]:
        return None


class ModelBuilder(ABC, Builder[PathModel, TModel]):

    def setup(self, **kwargs) -> None:
        pass

    @abstractmethod
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

    @abstractmethod
    def build_model(self, entry: PathModel, **kwargs) -> Optional[TModel]:
        ...
