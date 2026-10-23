"""What is wrong with a configuration file, as data rather than an exception.

This package carries the same name as one that was deleted earlier in the
refactoring, and takes the opposite approach. That one was a framework of
validators traversing already-built rule objects - by which point the file,
the section and the key the value came from are gone, so it could never
produce a message worth reading, and nothing ever called it.

A problem here is recorded where the value is read, while the file and the
path to the key are still known, and problems are collected rather than
raised one at a time. That is also the shape a user interface needs: a list
to show, not an exception to catch.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """How badly a problem matters."""

    ERROR = "error"
    """The configuration cannot be used as written."""

    WARNING = "warning"
    """Usable, but almost certainly not what was meant."""


@dataclass(frozen=True)
class ConfigProblem:
    """One thing wrong in one configuration file.

    Parameters
    ----------
    file
        The configuration file, as the user would name it.
    location
        The path to the offending key, e.g.
        ``config.name.rules[0].equals``, so the line can be found without
        guessing.
    message
        What is wrong, and where possible what to write instead.
    severity
        :attr:`Severity.ERROR` if the configuration cannot be used.
    """

    file: str
    location: str
    message: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return f"{self.severity.value.upper():7} {self.file} [{self.location}]: {self.message}"


def has_errors(problems: Iterable[ConfigProblem]) -> bool:
    """Whether any of ``problems`` prevents the configuration from being used."""
    return any(problem.severity is Severity.ERROR for problem in problems)


def problem_report(problems: Iterable[ConfigProblem]) -> str:
    """The problems as lines, errors first, grouped by file."""
    ordered = sorted(
        problems,
        key=lambda problem: (problem.severity is not Severity.ERROR, problem.file, problem.location),
    )
    return "\n".join(str(problem) for problem in ordered)


class ConfigFileError(ValueError):
    """A configuration file could not be used, naming the file.

    Raised at the boundary where the file is still known, so that the
    failure a user sees says which of their files it came from.
    """

    def __init__(self, file: str, message: str) -> None:
        super().__init__(f"{file}: {message}")
        self.file = file
        self.reason = message
