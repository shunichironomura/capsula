from abc import ABC, abstractmethod
from typing import Any


class Context(ABC):
    @abstractmethod
    def encapsulate(self) -> Any:
        raise NotImplementedError
