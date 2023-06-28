from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from capsula.context import Context

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    ...


def monitor(args, *, config: MonitorConfig, context: Context):
    result = subprocess.run(args, capture_output=True, text=True)

    logger.info(result.stdout)
    logger.error(result.stderr)
    logger.info(result.returncode)
