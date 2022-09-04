from typing import Protocol


class Config(Protocol):

    def validate(self):
        ...
