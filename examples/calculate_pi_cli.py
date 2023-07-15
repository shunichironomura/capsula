import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
import matplotlib.pyplot as plt
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
def main(n: int, seed: Optional[int] = None) -> None:
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

    # Plot the results
    fig = plt.figure(figsize=(8, 8))

    # Plot the points
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(x, y, s=0.01, c="k")
    ax.set_aspect("equal")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    capsule_name = os.environ["CAPSULA_CAPSULE_NAME"]
    ax.set_title(f"Approximation of pi: {pi:.6f} ({capsule_name})")

    # Plot the circle
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), c="k")

    output_path = Path(__file__).parent / "pi_cli.png"
    fig.savefig(str(output_path), dpi=300)


if __name__ == "__main__":
    main()
