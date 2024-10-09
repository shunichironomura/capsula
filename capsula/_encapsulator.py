from __future__ import annotations

import queue
import threading
import warnings
from collections import OrderedDict
from itertools import chain
from typing import TYPE_CHECKING, Any, Union

from capsula._utils import ExceptionInfo

from ._capsule import Capsule
from ._context import ContextBase
from ._exceptions import CapsulaError
from ._watcher import WatcherBase, WatcherGroup

if TYPE_CHECKING:
    from types import TracebackType

    from ._backport import Self, TypeAlias

_CapsuleItemKey: TypeAlias = Union[str, tuple[str, ...]]


class KeyConflictError(CapsulaError):
    def __init__(self, key: _CapsuleItemKey) -> None:
        super().__init__(f"Capsule item with key {key} already exists.")


class ObjectContext(ContextBase):
    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def encapsulate(self) -> Any:
        return self.obj


class Encapsulator:
    _thread_local = threading.local()

    @classmethod
    def _get_context_stack(cls) -> queue.LifoQueue[Self]:
        if not hasattr(cls._thread_local, "context_stack"):
            cls._thread_local.context_stack = queue.LifoQueue()
        return cls._thread_local.context_stack  # type: ignore[no-any-return]

    @classmethod
    def get_current(cls) -> Self | None:
        try:
            return cls._get_context_stack().queue[-1]
        except IndexError:
            return None

    def __init__(self) -> None:
        self.contexts: OrderedDict[_CapsuleItemKey, ContextBase] = OrderedDict()
        self.watchers: OrderedDict[_CapsuleItemKey, WatcherBase] = OrderedDict()

    def __enter__(self) -> Self:
        self._get_context_stack().put(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._get_context_stack().get(block=False)

    def add_context(self, context: ContextBase, key: _CapsuleItemKey | None = None) -> None:
        if key is None:
            key = context.default_key()
        if key in self.contexts or key in self.watchers:
            raise KeyConflictError(key)
        self.contexts[key] = context

    def record(self, key: _CapsuleItemKey, record: Any) -> None:
        self.add_context(ObjectContext(record), key)

    def add_watcher(self, watcher: WatcherBase, key: _CapsuleItemKey | None = None) -> None:
        if key is None:
            key = watcher.default_key()
        if key in self.contexts or key in self.watchers:
            raise KeyConflictError(key)
        self.watchers[key] = watcher

    def encapsulate(self) -> Capsule:
        data = {}
        fails = {}
        for key, capsule_item in chain(self.contexts.items(), self.watchers.items()):
            try:
                data[key] = capsule_item.encapsulate()
            except Exception as e:  # noqa: PERF203
                if capsule_item.abort_on_error:
                    raise
                warnings.warn(f"Error occurred during encapsulation of {key}: {e}. Skipping.", stacklevel=3)
                fails[key] = ExceptionInfo.from_exception(e)
        return Capsule(data, fails)

    def watch(self) -> WatcherGroup[_CapsuleItemKey, WatcherBase]:
        return WatcherGroup(self.watchers)
