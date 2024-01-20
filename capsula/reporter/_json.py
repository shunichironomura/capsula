from __future__ import annotations

import logging
from pathlib import Path

from capsula.encapsulator import Capsule

from ._base import Reporter

logger = logging.getLogger(__name__)


class JsonDumpReporter(Reporter):
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def report(self, capsule: Capsule) -> None:
        logger.debug(f"Dumping capsule to {self.path}")
        # capsule.dump(self.path)
