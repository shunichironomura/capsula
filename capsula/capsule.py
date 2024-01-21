from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, TypeAlias

_ContextKey: TypeAlias = str | tuple[str, ...]


class Capsule:
    def __init__(self, data: Mapping[_ContextKey, Any]) -> None:
        self.data = dict(data)


class CapsuleItem(ABC):
    @abstractmethod
    def encapsulate(self) -> Any:
        raise NotImplementedError

    def default_key(self) -> str | tuple[str, ...]:
        msg = f"{self.__class__.__name__}.default_key() is not implemented"
        raise NotImplementedError(msg)
