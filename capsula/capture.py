__all__ = [
    "capture",
]

import logging
import subprocess

from capsula._context import ContextBase
from capsula.config import CapsulaConfig

logger = logging.getLogger(__name__)


def capture(*, config: CapsulaConfig) -> ContextBase:
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
        except subprocess.CalledProcessError:
            logger.exception(f"Pre-capture command failed: {command}")
            raise
        else:
            logger.info(f"Pre-capture command result: {result}")

    logger.info("Capturing the context.")

    config.ensure_capsule_directory_exists()

    ctx = ContextBase.capture(config)

    # Write the context to the output file.
    with (config.capsule / "context.json").open("w") as output_file:
        output_file.write(ctx.model_dump_json(indent=4))

    return ctx
