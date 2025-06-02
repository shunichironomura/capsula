from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import TypeAlias

    from typing_extensions import Self

    from capsula._run import CapsuleParams
    from capsula._utils import ExceptionInfo


_ContextKey: TypeAlias = str | tuple[str, ...]


class Capsule:
    def __init__(
        self,
        data: Mapping[_ContextKey, Any],
        fails: Mapping[_ContextKey, ExceptionInfo],
    ) -> None:
        self.data = dict(data)
        self.fails = dict(fails)


class CapsuleItem(ABC):
    @property
    @abstractmethod
    def abort_on_error(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def encapsulate(self) -> Any:
        raise NotImplementedError

    def default_key(self) -> str | tuple[str, ...]:
        msg = f"{self.__class__.__name__}.default_key() is not implemented"
        raise NotImplementedError(msg)

    @classmethod
    def builder(cls, *args: Any, **kwargs: Any) -> Callable[[CapsuleParams], Self]:
        def build(params: CapsuleParams) -> Self:  # type: ignore[type-var,misc] # noqa: ARG001
            return cls(*args, **kwargs)

        return build
