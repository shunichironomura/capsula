from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

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
def main(n: int, seed: int | None = None) -> None:
    """Calculate pi using the Monte Carlo method."""
    if n < 1:
        logger.error("n must be greater than or equal to 1.")
        sys.exit(1)
    logger.info(f"Calculating pi with {n} samples.")
    logger.debug(f"Seed: {seed}")
    random.seed(seed)
    xs = (random.random() for _ in range(n))
    ys = (random.random() for _ in range(n))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    pi_estimate = (4.0 * inside) / n
    logger.info(f"Pi estimate: {pi_estimate}")

    with (Path(__file__).parent / "pi_cli.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
