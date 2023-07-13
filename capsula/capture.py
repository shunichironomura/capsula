from __future__ import annotations

__all__ = [
    "capture",
]

import logging
import subprocess
from typing import TYPE_CHECKING

from capsula.context import Context
from capsula.globalvars import set_capsule_dir

if TYPE_CHECKING:
    from capsula.config import CapsulaConfig

logger = logging.getLogger(__name__)


def capture(*, config: CapsulaConfig) -> Context:
    """Capture the context."""
    logger.debug(f"Capture config: {config.capture}")

    for command in config.capture.pre_capture_commands:
        logger.info(f"Running pre-capture command: {command!r}")
        try:
            result = subprocess.run(
                command,
                shell=True,  # noqa: S602
                text=True,
                capture_output=True,
                check=True,
                cwd=config.root_directory,
            )
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
