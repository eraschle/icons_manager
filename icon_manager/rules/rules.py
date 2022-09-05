import os
from abc import ABC, abstractmethod
from typing import Any, Collection, Iterable, List

from icon_manager.helpers.path import Folder
from icon_manager.rules.base import IconRule, Operator
from icon_manager.rules.generate import (AfterGenerator, BeforeGenerator,
                                         BeforeOrAfterGenerator, CaseConverter,
                                         Generator, GeneratorManager)

# region FOLDER RULES


class FolderRule(IconRule):

    def __init__(self, attribute: str, operator: Operator,
                 values: Iterable[str], case_sensitive: bool,
                 before_or_after: bool, before_or_after_values: Collection[str]) -> None:
        self.attribute = attribute
        self.__values_generated = False
        self.__values = values
        self.operator = operator
        self.generator = GeneratorManager()
        self.__before_or_after = before_or_after
        self.generator.set_values(before_or_after_values)
        self.generator.converters = [CaseConverter(case_sensitive)]

    def get_generators(self) -> Iterable[Generator]:
        return [BeforeGenerator(), AfterGenerator(), BeforeOrAfterGenerator()]

    def before_and_after_generators(self) -> Iterable[Generator]:
        return [BeforeGenerator(), AfterGenerator()]

    def create_before_or_after(self, rule_values: Iterable[str]) -> Iterable[str]:
        self.generator.generators = self.get_generators()
        return self.generator.generates_unique(rule_values, include_value=True)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        if not self.__before_or_after:
            return
        self.generator.set_values(before_or_after)

    def create_rule_values(self, values: Iterable[str]) -> Iterable[str]:
        values = self.generator.converts(values)
        return self.create_before_or_after(values)

    @ property
    def rule_values(self) -> Iterable[str]:
        if not self.__values_generated:
            self.__values = self.create_rule_values(self.__values)
            self.__values_generated = True
        return self.__values

    def is_allowed(self, entry: Folder) -> bool:
        value = getattr(entry, self.attribute, None)
        if value is None or self.operator == Operator.UNKNOWN:
            return False
        value = self.generator.convert(value)
        return self.is_allowed_with_operator(entry, value)

    def are_any_allowed(self, entry: Folder, value: Any) -> bool:
        return any(self.is_value_allowed(entry, value, rule_value) for rule_value in self.rule_values)

    def are_all_allowed(self, entry: Folder, value: Any) -> bool:
        return all(self.is_value_allowed(entry, value, rule_value) for rule_value in self.rule_values)

    @ abstractmethod
    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        pass

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute} {self.__values}'

    def __repr__(self) -> str:
        return self.__str__()


class EqualsRule(FolderRule):

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        return rule_value == value


class NotEqualsRule(EqualsRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        return not super().is_value_allowed(entry, value, rule_value)


class ContainsRule(FolderRule):

    def get_generators(self) -> Iterable[Generator]:
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        return rule_value in value


class NotContainsRule(ContainsRule):

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        return not super().is_value_allowed(entry, value, rule_value)


class StartswithRule(FolderRule):

    def get_generators(self) -> Iterable[Generator]:
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        return value.startswith(rule_value)


class EndswithRule(FolderRule):

    def get_generators(self) -> Iterable[Generator]:
        return self.before_and_after_generators()

    def is_value_allowed(self, _: Folder, value: str, rule_value: str) -> bool:
        return value.endswith(rule_value)


class StartsOrEndswithRule(FolderRule):

    def get_generators(self) -> Iterable[Generator]:
        return self.before_and_after_generators()

    def is_value_allowed(self, entry: Folder, value: str, rule_value: str) -> bool:
        return value.startswith(rule_value) or value.endswith(rule_value)


class ContainsFileRule(FolderRule):

    def __init__(self, attribute: str, operator: Operator, values: Iterable[str],
                 case_sensitive: bool, before_or_after: bool,
                 before_or_after_values: Collection[str], level: int) -> None:
        super().__init__(attribute, operator, values, case_sensitive,
                         before_or_after, before_or_after_values)
        self.max_level = level
        self.replace_values = ['*', '.']

    def get_generators(self) -> Iterable[Generator]:
        return []

    def get_rule_value(self, value: str) -> str:
        for replace in self.replace_values:
            if not value.startswith(replace):
                continue
            value = value.lstrip(replace)
        return value

    def create_rule_values(self, values: Iterable[str]) -> Iterable[str]:
        values = map(lambda value: self.get_rule_value(value), values)
        return super().create_rule_values(values)

    def get_extensions_of(self, folder: Folder) -> Set[str]:
        extensions = [file.extension for file in folder.files]
        return set([ext for ext in extensions if ext is not None])

    def get_extensions(self, entry: Folder, level: int) -> Iterable[str]:
        if level > self.max_level:
            return []
        level += 1
        extensions = self.get_extensions_of(entry)
        for folder in entry.folders:
            extensions.update(self.get_extensions(folder, level))
        return extensions

    def is_value_allowed(self, entry: Folder, _: str, rule_value: str) -> bool:
        extensions = self.get_extensions(entry, level=0)
        return any(ext.endswith(rule_value) for ext in extensions)


# endregion


class ChainedRule(IconRule):

    def __init__(self, attribute: str, operator: Operator,
                 rules: Collection[IconRule]) -> None:
        super().__init__(attribute, operator)
        self.rules = rules

    def is_empty(self) -> bool:
        return self.rule_count() == 0

    def rule_count(self) -> int:
        return len(self.rules)

    def is_allowed(self, entry: Folder) -> bool:
        value = getattr(entry, self.attribute, None)
        if value is None:
            return False
        return self.is_allowed_with_operator(entry, value)

    def are_any_allowed(self, entry: Folder, _: str) -> bool:
        return any(rule.is_allowed(entry) for rule in self.rules)

    def are_all_allowed(self, entry: Folder, _: str) -> bool:
        return all(rule.is_allowed(entry) for rule in self.rules)

    def set_before_or_after(self, before_or_after: Iterable[str]) -> None:
        for rule in self.rules:
            rule.set_before_or_after(before_or_after)
