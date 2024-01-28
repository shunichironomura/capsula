from pathlib import Path

from ._base import ContextBase


class CwdContext(ContextBase):
    def encapsulate(self) -> Path:
        return Path.cwd()

    def default_key(self) -> str:
        return "cwd"
