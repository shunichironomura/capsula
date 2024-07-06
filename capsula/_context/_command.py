from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypedDict

from ._base import ContextBase

if TYPE_CHECKING:
    from capsula._run import CapsuleParams


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

    @classmethod
    def default(
        cls,
        command: str,
        *,
        cwd: Path | str | None = None,
        check: bool = True,
        abort_on_error: bool = True,
        cwd_relative_to_project_root: bool = False,
    ) -> Callable[[CapsuleParams], CommandContext]:
        def callback(params: CapsuleParams) -> CommandContext:
            if cwd_relative_to_project_root and cwd is not None and not Path(cwd).is_absolute():
                cwd_path: Path | None = params.project_root / cwd
            elif cwd_relative_to_project_root and cwd is None:
                cwd_path = params.project_root
            else:
                cwd_path = Path(cwd) if cwd is not None else None

            return cls(
                command,
                cwd=cwd_path,
                check=check,
                abort_on_error=abort_on_error,
            )

        return callback
