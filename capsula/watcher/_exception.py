from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta

from capsula.utils import ExceptionInfo

from ._base import Watcher

logger = logging.getLogger(__name__)


class UncaughtExceptionWatcher(Watcher):
    def __init__(self, name: str, *, base: type[BaseException] = Exception, reraise: bool = False) -> None:
        self.name = name
        self.base = base
        self.reraise = reraise
        self.exception: BaseException | None = None

    def encapsulate(self) -> ExceptionInfo:
        return ExceptionInfo.from_exception(self.exception)

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
