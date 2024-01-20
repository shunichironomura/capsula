from __future__ import annotations

import json
import logging
from pathlib import Path

from capsula.encapsulator import Capsule
from capsula.utils import to_nested_dict

from ._base import Reporter

logger = logging.getLogger(__name__)


class JsonDumpReporter(Reporter):
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Dumping capsule to {self.path}")

        def _str_to_tuple(s: str | tuple[str, ...]) -> tuple[str, ...]:
            if isinstance(s, str):
                return (s,)
            return s

        nested_data = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.data.items()})
        with self.path.open("w") as f:
            json.dump(nested_data, f, indent=2)
