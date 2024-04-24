from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

import orjson

from ._utils import capsule_to_nested_dict, create_default_encoder

if TYPE_CHECKING:
    from capsula._capsule import Capsule
    from capsula._run import CapsuleParams

from ._base import ReporterBase

logger = logging.getLogger(__name__)


class JsonDumpReporter(ReporterBase):
    def __init__(
        self,
        path: Path | str,
        *,
        default: Optional[Callable[[Any], Any]] = None,
        option: Optional[int] = None,
        mkdir: bool = True,
    ) -> None:
        self.path = Path(path)
        if mkdir:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        self.default_for_encoder = create_default_encoder(default)
        self.option = option

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Dumping capsule to {self.path}")

        nested_data = capsule_to_nested_dict(capsule)
        json_bytes = orjson.dumps(nested_data, default=self.default_for_encoder, option=self.option)
        self.path.write_bytes(json_bytes)

    @classmethod
    def default(
        cls,
        *,
        option: Optional[int] = None,
    ) -> Callable[[CapsuleParams], JsonDumpReporter]:
        def callback(params: CapsuleParams) -> JsonDumpReporter:
            return cls(
                params.run_dir / f"{params.phase}-run-report.json",
                option=orjson.OPT_INDENT_2 if option is None else option,
            )

        return callback
