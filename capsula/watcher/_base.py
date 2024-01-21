from __future__ import annotations

from abc import abstractmethod
from contextlib import AbstractContextManager

from capsula.capsule import CapsuleItem


class Watcher(CapsuleItem):
    @abstractmethod
    def watch(self) -> AbstractContextManager[None]:
        raise NotImplementedError
