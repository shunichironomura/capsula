import logging
import sys
from typing import Optional

import click

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-n",
    type=int,
    help="The number of samples to use.",
    default=1_000_000,
    show_default=True,
)
@click.option(
    "--seed",
    "-s",
    type=int,
    help="The seed to use for the random number generator passed to numpy.random.default_rng.",
    default=None,
)
def main(n: int, seed: Optional[int] = None) -> None:
    """Calculate pi using the Monte Carlo method."""
    if n < 1:
        logger.error("n must be greater than or equal to 1.")
        sys.exit(1)
    logger.info(f"Calculating pi with {n} samples.")
    logger.debug(f"Seed: {seed}")


if __name__ == "__main__":
    main()
