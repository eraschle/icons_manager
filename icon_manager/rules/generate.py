from abc import abstractmethod
from collections.abc import Collection, Iterable, Sequence
from typing import Protocol


class Converter(Protocol):
    def convert(self, value: str) -> str: ...

    def converts(self, values: Collection[str]) -> Collection[str]: ...


class CaseConverter(Converter):
    def __init__(self, case_sensitive: bool) -> None:
        super().__init__()
        self.case_sensitive = case_sensitive

    def convert(self, value: str) -> str:
        if self.case_sensitive:
            return value
        return value.lower()

    def converts(self, values: Collection[str]) -> Collection[str]:
        if self.case_sensitive:
            return values
        return [self.convert(value) for value in values]


class Generator(Protocol):
    def set_values(self, values: str | Iterable[str]): ...

    def generate(self, value: str) -> Collection[str]: ...

    def generate_unique(self, value: str) -> Collection[str]: ...


class ValueGenerator(Generator):
    def __init__(self) -> None:
        super().__init__()
        self.values: set[str] = set()

    def set_values(self, values: str | Iterable[str]):
        if isinstance(values, str):
            self.values.add(values)
        else:
            self.values.update(values)

    @abstractmethod
    def generate(self, value: str) -> Collection[str]: ...

    def generate_unique(self, value: str) -> Collection[str]:
        return set(self.generate(value))


class BeforeGenerator(ValueGenerator):
    def generate(self, value: str) -> Collection[str]:
        return [f"{before}{value}" for before in self.values]


class AfterGenerator(ValueGenerator):
    def generate(self, value: str) -> Collection[str]:
        return [f"{value}{after}" for after in self.values]


class BeforeOrAfterGenerator(AfterGenerator):
    def __generate(self, before: str, value: str) -> Iterable[str]:
        return [f"{before}{value}" for value in super().generate(value)]

    def generate(self, value: str) -> Collection[str]:
        values: list[str] = []
        for before in self.values:
            current_values = self.__generate(before, value)
            values.extend(current_values)
        return values


class GeneratorManager(ValueGenerator, Converter, Generator):
    def __init__(self) -> None:
        super().__init__()
        self.converters: Sequence[Converter] = []
        self.generators: Sequence[Generator] = []

    def set_generator_values(self, values: str | Iterable[str]):
        self.set_values(values)
        for generator in self.generators:
            generator.set_values(values)

    def convert(self, value: str) -> str:
        for converter in self.converters:
            value = converter.convert(value)
        return value

    def converts(self, values: Collection[str]) -> Collection[str]:
        converted = []
        for value in values:
            converted.append(self.convert(value))
        return converted

    def generate(self, value: str, include_value: bool = True) -> Collection[str]:
        generated_values: list[str] = []
        if include_value:
            generated_values.append(value)
        for generator in self.generators:
            generated_values.extend(generator.generate(value))
        return generated_values

    def generates(self, values: Collection[str], include_value: bool = True) -> Collection[str]:
        generated_values: list[str] = []
        for value in values:
            generated_values.extend(self.generate(value, include_value))
        return generated_values

    def generate_unique(self, value: str, include_value: bool = True) -> Collection[str]:
        generated_values: set[str] = set()
        if include_value:
            generated_values.add(value)
        for generator in self.generators:
            generated_values.update(generator.generate(value))
        return generated_values

    def generates_unique(self, values: Collection[str], include_value: bool = True) -> Collection[str]:
        generated: set[str] = set()
        for value in values:
            generated_values = self.generate_unique(value, include_value)
            generated.update(generated_values)
        return generated
