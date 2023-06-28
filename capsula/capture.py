from __future__ import annotations

import logging
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from capsula.context import Context

logger = logging.getLogger(__name__)


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class CaptureFileConfig(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"] = "sha256"
    copy_: bool = Field(default=True, alias="copy")


class GitConfig(BaseModel):
    repositories: dict[str, Path] = Field(default_factory=dict)


class CaptureConfig(BaseModel):
    """Configuration for the capture command."""

    vault_directory: Path
    capsule_template: str

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True # noqa: ERA001

    include_cpu: bool = True

    pre_capture_commands: list[str] = Field(default_factory=list)

    environment_variables: list[str] = Field(default_factory=list)

    files: dict[Path, CaptureFileConfig] = Field(default_factory=list)

    git: GitConfig = Field(default_factory=GitConfig)

    class Config:  # noqa: D106
        alias_generator = to_hyphen_case
        populate_by_name = False
        extra = "forbid"

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

    logger.debug(f"CWD: {Path.cwd()}")
    for command in config.pre_capture_commands:
        logger.debug(f"Running pre-capture command: {command}")
        result = subprocess.run(shlex.split(command), capture_output=True, text=True)  # noqa: S603
        logger.debug(f"Pre-capture command result: {result}")
        if result.returncode != 0:
            logger.error(f"Pre-capture command failed: {command}")
            logger.error(f"Pre-capture command stdout: {result.stdout}")
            logger.error(f"Pre-capture command stderr: {result.stderr}")
            msg = f"Pre-capture command failed: {command}"
            raise RuntimeError(msg)

    logger.info("Capturing the context.")

    try:
        config.capsule.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        logger.exception(f"Capsule already exists: {config.capsule}")
        raise

    ctx = Context.capture(config)

    # Write the context to the output file.
    with (config.capsule / "context.json").open("w") as output_file:
        output_file.write(ctx.model_dump_json(indent=4))

    return ctx
