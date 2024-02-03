from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ._base import ContextBase


class FunctionCallContext(ContextBase):
    def __init__(self, function: Callable, args: Sequence[Any], kwargs: Mapping[str, Any]) -> None:
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def encapsulate(self) -> dict:
        file_path = Path(inspect.getfile(self.function))
        _, first_line_no = inspect.getsourcelines(self.function)
        return {
            "file_path": file_path,
            "first_line_no": first_line_no,
            "args": self.args,
            "kwargs": self.kwargs,
        }

    def default_key(self) -> tuple[str, str]:
        return ("function", self.function.__name__)
