import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import capsula

logger = logging.getLogger(__name__)


@capsula.monitor(
    directory=Path(__file__).parents[1],
    include_return_value=True,
    items=("calculate-pi-dec",),
)
def main(n: int, seed: int | None = None) -> float:
    """Calculate pi using the Monte Carlo method."""
    if n < 1:
        msg = "n must be greater than or equal to 1."
        logger.error(msg)
        raise ValueError(msg)
    logger.info(f"Calculating pi with {n} samples.")
    logger.debug(f"Seed: {seed}")

    rng = np.random.default_rng(seed=seed)
    x = rng.random(n, dtype=np.float64)
    y = rng.random(n, dtype=np.float64)

    pi = float(4 * np.sum(x**2 + y**2 <= 1) / n)

    # Plot the results
    fig = plt.figure(figsize=(8, 8))

    # Plot the points
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(x, y, s=0.01, c="k")
    ax.set_aspect("equal")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"Approximation of pi: {pi:.6f}")

    # Plot the circle
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), c="k")

    # capsule_dir = Path(os.environ["CAPSULE_DIR"])
    # logger.info(f"Saving plot to {capsule_dir / 'pi.png'}")

    output_path = Path(__file__).parent / "pi_dec.png"
    fig.savefig(str(output_path), dpi=300)

    return pi


if __name__ == "__main__":
    main(1_000_000)
