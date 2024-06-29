from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from pathlib import Path

from ._base import ContextBase

logger = logging.getLogger(__name__)


class _CommandContextData(TypedDict):
    command: str
    cwd: Path | None
    returncode: int
    stdout: str
    stderr: str


class CommandContext(ContextBase):
    def __init__(
        self,
        command: str,
        *,
        cwd: Path | None = None,
        check: bool = True,
        abort_on_error: bool = True,
    ) -> None:
        self.command = command
        self.cwd = cwd
        self.check = check
        self.abort_on_error = abort_on_error

    def encapsulate(self) -> _CommandContextData:
        logger.debug(f"Running command: {self.command}")
        output = subprocess.run(  # noqa: S602
            self.command,
            shell=True,
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
