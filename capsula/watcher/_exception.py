from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta

from ._base import Watcher

logger = logging.getLogger(__name__)


class UncaughtExceptionWatcher(Watcher):
    def __init__(self, name: str, *, base: type[BaseException] = Exception, reraise: bool = False) -> None:
        self.name = name
        self.base = base
        self.reraise = reraise
        self.exception: BaseException | None = None

    def encapsulate(self) -> dict:
        return {
            "exc_type": type(self.exception).__name__ if self.exception is not None else None,
            "exc_value": self.exception,
            "traceback": self.exception.__traceback__ if self.exception is not None else None,
        }

    @contextmanager
    def watch(self) -> Iterator[None]:
        self.exception = None
        try:
            yield
        except self.base as e:
            logger.debug(f"UncaughtExceptionWatcher: {self.name} caught exception: {e}")
            self.exception = e
            if self.reraise:
                raise

    def default_key(self) -> tuple[str, str]:
        return ("exception", self.name)
