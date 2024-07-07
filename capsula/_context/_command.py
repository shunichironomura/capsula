from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypedDict

from typing_extensions import Annotated, Doc

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
    """Context to capture the output of a command run in a subprocess."""

    @classmethod
    def builder(
        cls,
        command: Annotated[str, Doc("Command to run")],
        *,
        cwd: Annotated[
            Path | str | None,
            Doc("Working directory for the command, passed to the `cwd` argument of `subprocess.run`"),
        ] = None,
        check: Annotated[
            bool,
            Doc(
                "Whether to raise an exception if the command returns a non-zero exit code, passed to the `check` "
                "argument of `subprocess.run",
            ),
        ] = True,
        abort_on_error: Annotated[
            bool,
            Doc("Whether to abort the encapsulation if the command returns a non-zero exit code"),
        ] = True,
        cwd_relative_to_project_root: Annotated[
            bool,
            Doc(
                "Whether `cwd` argument is relative to the project root. Will be ignored if `cwd` is None or absolute. "
                "If True, it will be interpreted as relative to the project root. "
                "If False, `cwd` will be interpreted as relative to the current working directory. "
                "It is recommended to set this to True in the configuration file.",
            ),
        ] = False,
    ) -> Callable[[CapsuleParams], CommandContext]:
        def build(params: CapsuleParams) -> CommandContext:
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

        return build

    def __init__(
        self,
        command: str,
        *,
        cwd: Path | None = None,
        check: bool = True,
        abort_on_error: bool = True,
    ) -> None:
        self._command = command
        self._cwd = cwd
        self._check = check
        self._abort_on_error = abort_on_error

    @property
    def abort_on_error(self) -> bool:
        return self._abort_on_error

    def encapsulate(self) -> _CommandContextData:
        logger.debug(f"Running command: {self._command}")
        output = subprocess.run(  # noqa: S602
            self._command,
            shell=True,
            text=True,
            capture_output=True,
            cwd=self._cwd,
            check=self._check,
        )
        logger.debug(f"Ran command: {self._command}. Result: {output}")
        return {
            "command": self._command,
            "cwd": self._cwd,
            "returncode": output.returncode,
            "stdout": output.stdout,
            "stderr": output.stderr,
        }

    def default_key(self) -> tuple[str, str]:
        return ("command", self._command)
