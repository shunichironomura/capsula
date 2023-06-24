import logging
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from capsula.environment import Environment

logger = logging.getLogger(__name__)


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class CaptureConfig(BaseModel):
    """Configuration for the capture command."""

    vault_directory: Path
    subdirectory_template: str

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True # noqa: ERA001

    include_cpu: bool = True

    pre_capture_commands: list[str] = Field(default_factory=list)

    files: list[Path] = Field(default_factory=list)

    git_repositories: list[Path] = Field(default_factory=list)

    class Config:  # noqa: D106
        alias_generator = to_hyphen_case
        populate_by_name = False
        extra = "forbid"


def capture(
    *,
    config: CaptureConfig,
    output: Path | None = None,
) -> None:
    """Capture the environment."""
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

    logger.info("Freezing the environment.")

    subdirectory = config.vault_directory / datetime.now(tz=None).strftime(config.subdirectory_template)  # noqa: DTZ005
    if config.files:
        subdirectory.mkdir(parents=True, exist_ok=True)
    for file in config.files:
        logger.debug(f"Adding file: {file.absolute()}")
        # Copy the file into the subdirectory.
        shutil.copy2(file, subdirectory)

    kwargs = {}
    if not config.include_cpu:
        kwargs["cpu"] = None
    env = Environment.capture(config)

    # Write the environment to the output file.
    env_json = env.model_dump_json(
        indent=4,
    )
    if output is None:
        sys.stdout.write(env_json)
    else:
        with output.open("w") as output_file:
            output_file.write(env_json)
