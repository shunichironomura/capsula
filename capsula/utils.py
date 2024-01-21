from __future__ import annotations

import traceback
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Hashable, TypedDict


@dataclass
class ExceptionInfo:
    exc_type: type[BaseException] | None
    exc_value: BaseException | None
    traceback: TracebackType | None

    @classmethod
    def from_exception(cls, exception: BaseException | None) -> ExceptionInfo:
        if exception is None:
            return cls(exc_type=None, exc_value=None, traceback=None)
        return cls(
            exc_type=type(exception),
            exc_value=exception,
            traceback=exception.__traceback__,
        )

    def as_json(self) -> dict[str, str | None]:
        return {
            "exc_type": self.exc_type.__name__ if self.exc_type is not None else None,
            "exc_value": str(self.exc_value) if self.exc_value is not None else None,
            "traceback": "".join(traceback.format_tb(self.traceback)) if self.traceback is not None else None,
        }


def to_flat_dict(
    nested_dict: Mapping[Hashable, Any],
    *,
    _preceding_keys: Sequence[Hashable] = (),
) -> dict[Sequence[Hashable], Any]:
    """Convert a nested dictionary to a flat dictionary.

    For example:
    >>> d = {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}}}
    >>> to_flat_dict(d)
    {("a",): 1, ("b", "c"): 2, ("b", "d"): 3, ("e", "f", "g"): 4}
    """
    flat_dict: dict[Sequence[Hashable], Any] = {}
    for key, value in nested_dict.items():
        if isinstance(value, Mapping):
            flat_dict.update(to_flat_dict(value, _preceding_keys=(*tuple(_preceding_keys), key)))
        else:
            flat_dict[(*tuple(_preceding_keys), key)] = value
    return flat_dict


def to_nested_dict(flat_dict: Mapping[Sequence[Hashable], Any]) -> dict[Hashable, Any]:
    """Convert a flat dictionary to a nested dictionary.

    For example:
    >>> d = {("a",): 1, ("b", "c"): 2, ("b", "d"): 3, ("e", "f", "g"): 4}
    >>> to_nested_dict(d)
    {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}}}
    """
    nested_dict: dict[Hashable, Any] = {}
    for key, value in flat_dict.items():
        if len(key) == 1:
            if key[0] in nested_dict:
                conflicting_value_as_fd = next(iter(to_flat_dict(nested_dict[key[0]])))
                conflicting_key = (key[0], *conflicting_value_as_fd)
                msg = f"Key conflicted: {key[0]} and {conflicting_key}"
                raise ValueError(msg)
            nested_dict[key[0]] = value
        elif key[0] in nested_dict:
            if not isinstance(nested_dict[key[0]], Mapping):
                msg = f"Key conflicted: {key[0]}"
                raise ValueError(msg)
            nested_dict[key[0]].update(to_nested_dict({key[1:]: value}))
        else:
            nested_dict[key[0]] = to_nested_dict({key[1:]: value})
    return nested_dict
