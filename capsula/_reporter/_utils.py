from __future__ import annotations

import traceback
from datetime import timedelta
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Hashable

from capsula.utils import to_nested_dict

if TYPE_CHECKING:
    from capsula._capsule import Capsule


def _default_preset(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, timedelta):
        return str(obj)
    if isinstance(obj, type) and issubclass(obj, BaseException):
        return obj.__name__
    if isinstance(obj, Exception):
        return str(obj)
    if isinstance(obj, TracebackType):
        return "".join(traceback.format_tb(obj))
    raise TypeError


def create_default_encoder(default: Callable[[Any], Any] | None = None) -> Callable[[Any], Any]:
    if default is None:
        return _default_preset
    else:

        def _default(obj: Any) -> Any:
            try:
                return _default_preset(obj)
            except TypeError:
                return default(obj)

        return _default


def capsule_to_nested_dict(capsule: Capsule) -> dict[Hashable, Any]:
    def _str_to_tuple(s: str | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(s, str):
            return (s,)
        return s

    nested_data = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.data.items()})
    if capsule.fails:
        nested_data["__fails"] = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.fails.items()})

    return nested_data
