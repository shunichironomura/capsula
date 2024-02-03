from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from ._base import ContextBase

logger = logging.getLogger(__name__)


class CommandContext(ContextBase):
    def __init__(self, command: str, *, cwd: Path | None = None, check: bool = False) -> None:
        self.command = command
        self.cwd = cwd
        self.check = check

    def encapsulate(self) -> dict:
        logger.debug(f"Running command: {self.command}")
        output = subprocess.run(
            self.command,
            shell=True,  # noqa: S602
            text=True,
            capture_output=True,
            cwd=self.cwd,
            check=self.check,
        )
        logger.debug(f"Ran command: {self.command}. Result: {output}")
        return {
            "command": self.command,
            "cwd": self.cwd,
            "returncode": output.returncode,
            "stdout": output.stdout,
            "stderr": output.stderr,
        }

    def default_key(self) -> tuple[str, str]:
        return ("command", self.command)
