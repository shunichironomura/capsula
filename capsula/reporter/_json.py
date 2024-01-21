from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from capsula.encapsulator import Capsule
from capsula.utils import to_nested_dict

from ._base import Reporter

logger = logging.getLogger(__name__)


class CapsuleDataJsonEncoder(json.JSONEncoder):
    """A JSON encoder for Capsule.data.

    You can inherit from this class and override the default method to add more
    types.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, timedelta):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class JsonDumpReporter(Reporter):
    def __init__(self, path: Path | str, **kwargs: Any) -> None:
        self.path = Path(path)
        self.kwargs = kwargs

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Dumping capsule to {self.path}")

        def _str_to_tuple(s: str | tuple[str, ...]) -> tuple[str, ...]:
            if isinstance(s, str):
                return (s,)
            return s

        nested_data = to_nested_dict({_str_to_tuple(k): v for k, v in capsule.data.items()})

        json_encoder = self.kwargs.pop("cls", CapsuleDataJsonEncoder)
        with self.path.open("w") as f:
            json.dump(nested_data, f, cls=json_encoder, **self.kwargs)
