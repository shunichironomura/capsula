from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Hashable, TypeVar

_T = TypeVar("_T")


def to_nested_dict(flat_dict: Mapping[Sequence[Hashable], _T]) -> dict[Hashable, Any]:
    """Convert a flat dictionary to a nested dictionary.

    For example:
    >>> d = {("a",): 1, ("b", "c"): 2, ("b", "d"): 3, ("e", "f", "g"): 4}
    >>> to_nested_dict(d)
    {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}}}
    """
    nested_dict: dict[Hashable, Any] = {}
    for key, value in flat_dict.items():
        if len(key) == 1:
            nested_dict[key[0]] = value
        else:
            nested_dict[key[0]] = to_nested_dict({key[1:]: value})
    return nested_dict
