import logging
import sys

import click
import numpy as np

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
def main(n: int, seed: int | None = None) -> None:
    """Calculate pi using the Monte Carlo method."""
    if n < 1:
        logger.error("n must be greater than or equal to 1.")
        sys.exit(1)
    logger.info(f"Calculating pi with {n} samples.")
    logger.debug(f"Seed: {seed}")
    rng = np.random.default_rng(seed)
    x = rng.random(n, dtype=np.float64)
    y = rng.random(n, dtype=np.float64)
    pi = float(4 * np.sum(x**2 + y**2 <= 1) / n)
    sys.stdout.write(f"{pi}\n")


if __name__ == "__main__":
    main()
