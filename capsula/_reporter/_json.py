from __future__ import annotations

import logging
import traceback
from datetime import timedelta
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable

import orjson

from capsula.utils import to_nested_dict

if TYPE_CHECKING:
    from capsula._capsule import Capsule
    from capsula._run import CapsuleParams

from ._base import ReporterBase

logger = logging.getLogger(__name__)


def default_preset(obj: Any) -> Any:
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


class JsonDumpReporter(ReporterBase):
    def __init__(
        self,
        path: Path | str,
        *,
        default: Callable[[Any], Any] | None = None,
        option: int | None = None,
        mkdir: bool = True,
    ) -> None:
        self.path = Path(path)
        if mkdir:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        if default is None:
            self.default_for_encoder = default_preset
        else:

            def _default(obj: Any) -> Any:
                try:
                    return default_preset(obj)
                except TypeError:
                    return default(obj)

            self.default_for_encoder = _default

        self.option = option

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Dumping capsule to {self.path}")

        def _str_to_tuple(s: str | tuple[str, ...]) -> tuple[str, ...]:
            if isinstance(s, str):
                return (s,)
            return s

        nested_data = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.data.items()})
        if capsule.fails:
            nested_data["__fails"] = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.fails.items()})

        json_bytes = orjson.dumps(nested_data, default=self.default_for_encoder, option=self.option)
        self.path.write_bytes(json_bytes)

    @classmethod
    def default(
        cls,
        *,
        option: int | None = None,
    ) -> Callable[[CapsuleParams], JsonDumpReporter]:
        def callback(params: CapsuleParams) -> JsonDumpReporter:
            return cls(
                params.run_dir / f"{params.phase}-run-report.json",
                option=orjson.OPT_INDENT_2 if option is None else option,
            )

        return callback
