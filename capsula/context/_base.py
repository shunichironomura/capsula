from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Context(ABC):
    @abstractmethod
    def encapsulate(self) -> Any:
        raise NotImplementedError

    def default_key(self) -> str | tuple[str, ...]:
        msg = f"{self.__class__.__name__}.default_key() is not implemented"
        raise NotImplementedError(msg)
