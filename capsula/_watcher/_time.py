from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from ._base import WatcherBase

logger = logging.getLogger(__name__)


class TimeWatcher(WatcherBase):
    def __init__(self, name: str = "execution_time") -> None:
        self.name = name
        self.duration: timedelta | None = None

    def encapsulate(self) -> timedelta | None:
        return self.duration

    @contextmanager
    def watch(self) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self.duration = timedelta(seconds=end - start)
            logger.debug(f"TimeWatcher: {self.name} took {self.duration}.")

    def default_key(self) -> tuple[str, str]:
        return ("time", self.name)
