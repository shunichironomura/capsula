from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta

from ._base import Watcher

logger = logging.getLogger(__name__)


class TimeWatcher(Watcher):
    def __init__(self, name: str) -> None:
        self.name = name
        self.duration: timedelta | None = None

    def encapsulate(self) -> timedelta | None:
        return self.duration

    @contextmanager
    def watch(self) -> Iterator[None]:
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        self.duration = timedelta(seconds=end - start)
        logger.debug(f"TimeWatcher: {self.name} took {self.duration}.")

    def default_key(self) -> tuple[str, str]:
        return ("time", self.name)
