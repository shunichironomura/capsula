from __future__ import annotations

import os
from typing import Annotated

from typing_extensions import Doc

from ._base import ContextBase


class EnvVarContext(ContextBase):
    """Context to capture an environment variable."""

    def __init__(self, name: Annotated[str, Doc("Name of the environment variable")]) -> None:
        self.name = name

    def encapsulate(self) -> str | None:
        return os.getenv(self.name)

    def default_key(self) -> tuple[str, str]:
        return ("env", self.name)
