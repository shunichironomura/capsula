from __future__ import annotations

import os

from ._base import ContextBase


class EnvVarContext(ContextBase):
    def __init__(self, name: str) -> None:
        self.name = name

    def encapsulate(self) -> str | None:
        return os.getenv(self.name)

    def default_key(self) -> tuple[str, str]:
        return ("env", self.name)
