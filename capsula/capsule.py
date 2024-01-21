from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Tuple, Union

if TYPE_CHECKING:
    from collections.abc import Mapping

    from capsula.utils import ExceptionInfo

    from ._backport import TypeAlias


_ContextKey: TypeAlias = Union[str, Tuple[str, ...]]


class Capsule:
    def __init__(
        self,
        data: Mapping[_ContextKey, Any],
        fails: Mapping[_ContextKey, ExceptionInfo],
    ) -> None:
        self.data = dict(data)
        self.fails = dict(fails)


class CapsuleItem(ABC):
    @abstractmethod
    def encapsulate(self) -> Any:
        raise NotImplementedError

    def default_key(self) -> str | tuple[str, ...]:
        msg = f"{self.__class__.__name__}.default_key() is not implemented"
        raise NotImplementedError(msg)
