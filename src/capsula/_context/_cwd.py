from pathlib import Path

from ._base import ContextBase


class CwdContext(ContextBase):
    """Context to capture the current working directory."""

    def encapsulate(self) -> Path:
        return Path.cwd()

    def default_key(self) -> str:
        return "cwd"
