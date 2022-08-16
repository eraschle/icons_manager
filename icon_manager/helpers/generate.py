from abc import abstractmethod
from typing import Iterable, List, Protocol, Set, Union


class ValueGenerator(Protocol):

    def generate(self, value: str) -> str:
        ...

    def generates(self, values: Iterable[str]) -> Iterable[str]:
        ...


class CaseGenerator(ValueGenerator):

    def __init__(self, case_sensitive: bool) -> None:
        super().__init__()
        self.case_sensitive = case_sensitive

    def generate(self, value: str) -> str:
        if self.case_sensitive:
            return value
        return value.lower()

    def generates(self, values: Iterable[str]) -> Iterable[str]:
        if self.case_sensitive:
            return values
        return [self.generate(value) for value in values]


class ValuesGenerator(Protocol):

    def set_generation_values(self, generation_values: Union[str, Iterable[str]]):
        ...

    def generate_many(self, value: str) -> Iterable[str]:
        ...

    def generate_many_unique(self, value: str) -> Iterable[str]:
        ...


class AValuesGenerator(ValuesGenerator):

    def __init__(self) -> None:
        super().__init__()
        self.generation_values: Set[str] = set()

    def set_generation_values(self, generation_values: Union[str, Iterable[str]]):
        if isinstance(generation_values, str):
            self.generation_values.add(generation_values)
        else:
            self.generation_values.update(generation_values)

    @abstractmethod
    def generate_many(self, value: str) -> Iterable[str]:
        ...

    def generate_many_unique(self, value: str) -> Iterable[str]:
        return set(self.generate_many(value))


class BeforeValueGenerator(AValuesGenerator):

    def generate_many(self, value: str) -> Iterable[str]:
        return [f'{before}{value}' for before in self.generation_values]


class AfterValueGenerator(AValuesGenerator):

    def generate_many(self, value: str) -> Iterable[str]:
        return [f'{value}{after}' for after in self.generation_values]


class BeforeOrAfterValuesGenerator(AfterValueGenerator):

    def __generate(self, before: str, value: str) -> Iterable[str]:
        return [f'{before}{value}' for value in super().generate_many(value)]

    def generate_many(self, value: str) -> Iterable[str]:
        values: List[str] = []
        for before in self.generation_values:
            current_values = self.__generate(before, value)
            values.extend(current_values)
        return values


class Generator(AValuesGenerator, ValueGenerator, ValuesGenerator):
    def __init__(self) -> None:
        super().__init__()
        self.value_generators: Iterable[ValueGenerator] = []
        self.values_generators: Iterable[ValuesGenerator] = []

    def generate(self, value: str) -> str:
        for generator in self.value_generators:
            value = generator.generate(value)
        return value

    def generates(self, values: Iterable[str]) -> Iterable[str]:
        generated_values = []
        for value in values:
            generated_values.append(self.generate(value))
        return generated_values

    def generate_many(self, value: str, include_value: bool = True) -> Iterable[str]:
        generated_values: List[str] = []
        if include_value:
            generated_values.append(value)
        for generator in self.values_generators:
            generator.set_generation_values(self.generation_values)
            generated_values.extend(generator.generate_many(value))
        return generated_values

    def generates_many(self, values: Iterable[str], include_value: bool = True) -> Iterable[str]:
        generated_values: List[str] = []
        for value in values:
            generated_values.extend(self.generate_many(value, include_value))
        return generated_values

    def generate_many_unique(self, value: str, include_value: bool = True) -> Iterable[str]:
        generated_values: Set[str] = set()
        if include_value:
            generated_values.add(value)
        for generator in self.values_generators:
            generator.set_generation_values(self.generation_values)
            generated_values.update(generator.generate_many(value))
        return generated_values

    def generates_many_unique(self, values: Iterable[str], include_value: bool = True) -> Iterable[str]:
        generated_values: List[str] = []
        for value in values:
            generated_values.extend(
                self.generate_many_unique(value, include_value))
        return generated_values
