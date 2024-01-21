from pathlib import Path

from ._base import Context


class CwdContext(Context):
    def encapsulate(self) -> Path:
        return Path.cwd()

    def default_key(self) -> str:
        return "cwd"
