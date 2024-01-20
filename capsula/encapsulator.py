from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self, TypeAlias

from .context import Context
from .exceptions import CapsulaError

_ContextKey: TypeAlias = str | tuple[str, ...]
_JsonValue: TypeAlias = str | int | float | bool | None | list["_JsonValue"] | dict[str, "_JsonValue"]


class KeyConflictError(CapsulaError):
    def __init__(self, key: _ContextKey) -> None:
        super().__init__(f"Context with key {key} already exists")


class ObjectContext(Context):
    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def encapsulate(self) -> Any:
        return self.obj


class Capsule:
    def __init__(self, data: Mapping[_ContextKey, _JsonValue]) -> None:
        self.data = dict(data)


class Encapsulator:
    def __init__(self) -> None:
        self.contexts: OrderedDict[_ContextKey, Context] = OrderedDict()

    def add_context(self, context: Context, key: _ContextKey | None = None) -> None:
        if key is None:
            key = context.default_key()
        if key in self.contexts:
            raise KeyConflictError(key)
        self.contexts[key] = context

    def record(self, key: _ContextKey, record: Any) -> None:
        self.add_context(ObjectContext(record), key)

    def encapsulate(self) -> Capsule:
        return Capsule({key: context.encapsulate() for key, context in self.contexts.items()})

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass
