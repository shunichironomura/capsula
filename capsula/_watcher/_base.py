from __future__ import annotations

import queue
from abc import ABC, abstractmethod
from collections.abc import Hashable
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar

from capsula._capsule import CapsuleItem

if TYPE_CHECKING:
    from collections import OrderedDict
    from types import TracebackType


class WatcherBase(CapsuleItem, ABC):
    _subclass_registry: Final[dict[str, type[WatcherBase]]] = {}

    @property
    def abort_on_error(self) -> bool:
        return False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if cls.__name__ in cls._subclass_registry:
            msg = f"Duplicate watcher name: {cls.__name__}"
            raise ValueError(msg)
        cls._subclass_registry[cls.__name__] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def get_subclass(cls, name: str) -> type[WatcherBase]:
        return cls._subclass_registry[name]

    @abstractmethod
    def watch(self) -> AbstractContextManager[None]:
        raise NotImplementedError


_K = TypeVar("_K", bound=Hashable)
_V = TypeVar("_V", bound=WatcherBase)


class WatcherGroup(Generic[_K, _V], AbstractContextManager[dict[_K, Any]]):
    def __init__(self, watchers: OrderedDict[_K, _V]) -> None:
        self.watchers = watchers
        self.context_manager_stack: queue.LifoQueue[AbstractContextManager[None]] = queue.LifoQueue()

    def __enter__(self) -> dict[_K, Any]:
        self.context_manager_stack = queue.LifoQueue()
        cm_dict = {}
        for key, watcher in reversed(self.watchers.items()):
            cm = watcher.watch()
            self.context_manager_stack.put(cm)
            cm_dict[key] = cm
            cm.__enter__()
        return cm_dict

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        suppress_exception = False

        while not self.context_manager_stack.empty():
            cm = self.context_manager_stack.get(block=False)
            suppress = bool(cm.__exit__(exc_type, exc_value, traceback))
            suppress_exception = suppress_exception or suppress

            # If the current context manager handled the exception, we clear the exception info.
            if suppress:
                exc_type, exc_value, traceback = None, None, None

        # Return True if any context manager in the stack handled the exception.
        return suppress_exception
