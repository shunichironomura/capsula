from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from capsula._utils import ExceptionInfo

from ._base import WatcherBase

logger = logging.getLogger(__name__)


class UncaughtExceptionWatcher(WatcherBase):
    def __init__(
        self,
        name: str = "exception",
        *,
        base: type[BaseException] = Exception,
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
