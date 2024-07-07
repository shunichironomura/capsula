from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TypedDict

from ._base import ContextBase


class _FunctionCallContextData(TypedDict):
    file_path: Path
    first_line_no: int
    args: Sequence[Any]
    kwargs: Mapping[str, Any]


class FunctionCallContext(ContextBase):
    def __init__(self, function: Callable[..., Any], args: Sequence[Any], kwargs: Mapping[str, Any]) -> None:
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def encapsulate(self) -> _FunctionCallContextData:
        file_path = Path(inspect.getfile(self._function))
        _, first_line_no = inspect.getsourcelines(self._function)
        return {
            "file_path": file_path,
            "first_line_no": first_line_no,
            "args": self._args,
            "kwargs": self._kwargs,
        }

    def default_key(self) -> tuple[str, str]:
        return ("function", self._function.__name__)
