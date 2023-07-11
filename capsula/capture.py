from __future__ import annotations

import logging
import subprocess
import sys

if sys.version_info < (3, 11):
    from datetime import timezone as _timezone

    UTC = _timezone.utc

else:
    from datetime import UTC
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from capsula.context import Context
from capsula.file import CaptureFileConfig  # noqa: TCH001 for pydantic
from capsula.globalvars import set_capsule_dir

logger = logging.getLogger(__name__)


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class GitConfig(BaseModel):
    repositories: dict[str, Path] = Field(default_factory=dict)


class CaptureConfig(BaseModel):
    """Configuration for the capture command."""

    model_config = ConfigDict(
        alias_generator=to_hyphen_case,
        populate_by_name=True,
        extra="forbid",
    )

    vault_directory: Path
    capsule_template: str

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True

    include_cpu: bool = True

    pre_capture_commands: list[str] = Field(default_factory=list)

    environment_variables: list[str] = Field(default_factory=list)

    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)

    git: GitConfig = Field(default_factory=GitConfig)

    _capsule_directory: Path | None = None

    @property
    def capsule(self) -> Path:
        if self._capsule_directory is None:
            self._capsule_directory = self.vault_directory / datetime.now(UTC).astimezone().strftime(
                self.capsule_template,
            )
        return self._capsule_directory


def capture(*, config: CaptureConfig) -> Context:
    """Capture the context."""
    logger.debug(f"Capture config: {config}")

    logger.info(f"CWD: {Path.cwd()}")
    for command in config.pre_capture_commands:
        logger.info(f"Running pre-capture command: {command!r}")
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)  # noqa: S602
        except subprocess.CalledProcessError:  # noqa: PERF203
            logger.exception(f"Pre-capture command failed: {command}")
            raise
        else:
            logger.info(f"Pre-capture command result: {result}")

    logger.info("Capturing the context.")

    try:
        config.capsule.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        logger.exception(f"Capsule already exists: {config.capsule}")
        raise
    else:
        set_capsule_dir(config.capsule)

    ctx = Context.capture(config)

    # Write the context to the output file.
    with (config.capsule / "context.json").open("w") as output_file:
        output_file.write(ctx.model_dump_json(indent=4))

    return ctx
