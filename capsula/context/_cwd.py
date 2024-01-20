from pathlib import Path
from typing import Any

from ._base import Context


class CwdContext(Context):
    def encapsulate(self) -> Any:
        return str(Path.cwd())
