from __future__ import annotations

import queue
import threading
from collections import OrderedDict
from collections.abc import Hashable
from contextlib import AbstractContextManager
from itertools import chain
from typing import TYPE_CHECKING, Any, Generic, Self, Tuple, TypeVar, Union

if TYPE_CHECKING:
    from ._backport import TypeAlias

if TYPE_CHECKING:
    from types import TracebackType

from capsula.utils import ExceptionInfo

from ._capsule import Capsule
from .context import Context
from .exceptions import CapsulaError
from .watcher import Watcher

_CapsuleItemKey: TypeAlias = Union[str, Tuple[str, ...]]


class KeyConflictError(CapsulaError):
    def __init__(self, key: _CapsuleItemKey) -> None:
        super().__init__(f"Capsule item with key {key} already exists.")


class ObjectContext(Context):
    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def encapsulate(self) -> Any:
        return self.obj


_K = TypeVar("_K", bound=Hashable)
_V = TypeVar("_V", bound=Watcher)


class WatcherGroup(AbstractContextManager, Generic[_K, _V]):
    def __init__(self, watchers: OrderedDict[_K, _V]) -> None:
        self.watchers = watchers
        self.context_manager_stack: queue.LifoQueue[AbstractContextManager] = queue.LifoQueue()

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
            cm = self.context_manager_stack.get()
            suppress = bool(cm.__exit__(exc_type, exc_value, traceback))
            suppress_exception = suppress_exception or suppress

            # If the current context manager handled the exception, we clear the exception info.
            if suppress:
                exc_type, exc_value, traceback = None, None, None

        # Return True if any context manager in the stack handled the exception.
        return suppress_exception


class Encapsulator:
    _thread_local = threading.local()

    @classmethod
    def _get_context_stack(cls) -> queue.LifoQueue[Self]:
        if not hasattr(cls._thread_local, "encapsulator_context_stack"):
            cls._thread_local.encapsulator_context_stack = queue.LifoQueue()
        return cls._thread_local.encapsulator_context_stack

    @classmethod
    def get_current(cls) -> Self | None:
        try:
            return cls._get_context_stack().queue[-1]
        except IndexError:
            return None

    def __init__(self) -> None:
        self.contexts: OrderedDict[_CapsuleItemKey, Context] = OrderedDict()
        self.watchers: OrderedDict[_CapsuleItemKey, Watcher] = OrderedDict()

    def __enter__(self) -> Self:
        self._get_context_stack().put(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._get_context_stack().get()

    def add_context(self, context: Context, key: _CapsuleItemKey | None = None) -> None:
        if key is None:
            key = context.default_key()
        if key in self.contexts or key in self.watchers:
            raise KeyConflictError(key)
        self.contexts[key] = context

    def record(self, key: _CapsuleItemKey, record: Any) -> None:
        self.add_context(ObjectContext(record), key)

    def add_watcher(self, watcher: Watcher, key: _CapsuleItemKey | None = None) -> None:
        if key is None:
            key = watcher.default_key()
        if key in self.contexts or key in self.watchers:
            raise KeyConflictError(key)
        self.watchers[key] = watcher

    def encapsulate(self, *, abort_on_error: bool = False) -> Capsule:
        data = {}
        fails = {}
        for key, capsule_item in chain(self.contexts.items(), self.watchers.items()):
            try:
                data[key] = capsule_item.encapsulate()
            except Exception as e:  # noqa: PERF203,BLE001
                if abort_on_error:
                    raise
                fails[key] = ExceptionInfo.from_exception(e)
        return Capsule(data, fails)

    def watch(self) -> WatcherGroup[_CapsuleItemKey, Watcher]:
        return WatcherGroup(self.watchers)
