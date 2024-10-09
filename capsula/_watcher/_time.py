from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import TYPE_CHECKING, Annotated

from typing_extensions import Doc

if TYPE_CHECKING:
    from collections.abc import Iterator

from ._base import WatcherBase

logger = logging.getLogger(__name__)


class TimeWatcher(WatcherBase):
    def __init__(
        self,
        name: Annotated[str, Doc("Name of the time watcher. Used as a key in the output.")] = "execution_time",
    ) -> None:
        self._name = name
        self._duration: timedelta | None = None

    def encapsulate(self) -> timedelta | None:
        return self._duration

    @contextmanager
    def watch(self) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self._duration = timedelta(seconds=end - start)
            logger.debug(f"TimeWatcher: {self._name} took {self._duration}.")

    def default_key(self) -> tuple[str, str]:
        return ("time", self._name)
