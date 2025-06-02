from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Annotated

from typing_extensions import Doc

if TYPE_CHECKING:
    from collections.abc import Iterator

from capsula._utils import ExceptionInfo

from ._base import WatcherBase

logger = logging.getLogger(__name__)


class UncaughtExceptionWatcher(WatcherBase):
    """Watcher to capture an uncaught exception.

    This watcher captures an uncaught exception and stores it in the context.
    Note that it does not consume the exception, so it will still be raised.
    """

    def __init__(
        self,
        name: Annotated[str, Doc("Name of the exception. Used as a key in the output.")] = "exception",
        *,
        base: Annotated[type[BaseException], Doc("Base exception class to catch.")] = Exception,
    ) -> None:
        self._name = name
        self._base = base
        self._exception: BaseException | None = None

    def encapsulate(self) -> ExceptionInfo:
        return ExceptionInfo.from_exception(self._exception)

    @contextmanager
    def watch(self) -> Iterator[None]:
        self._exception = None
        try:
            yield
        except self._base as e:
            logger.debug(f"UncaughtExceptionWatcher: {self._name} observed exception: {e}")
            self._exception = e
            raise

    def default_key(self) -> tuple[str, str]:
        return ("exception", self._name)
