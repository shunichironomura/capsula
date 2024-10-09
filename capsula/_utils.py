from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from typing_extensions import Doc

if TYPE_CHECKING:
    from types import TracebackType


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


def search_for_project_root(
    start: Annotated[Path | str, Doc("The start directory to search.")],
) -> Annotated[Path, Doc("The project root directory.")]:
    """Search for the project root directory by looking for pyproject.toml."""
    # TODO: Allow projects without pyproject.toml file
    start = Path(start)
    if (start / "pyproject.toml").exists():
        return start
    if start == start.parent:
        msg = "Project root not found."
        raise FileNotFoundError(msg)
    return search_for_project_root(start.resolve().parent)


def get_default_config_path() -> Path:
    config_path = search_for_project_root(Path.cwd()) / "capsula.toml"
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)
    return config_path
