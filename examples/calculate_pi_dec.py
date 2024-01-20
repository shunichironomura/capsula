import logging
import random
from pathlib import Path
from typing import Optional

import capsula

logger = logging.getLogger(__name__)


@capsula.monitor(
    directory=Path(__file__).parents[1],
    include_return_value=True,
    items=("calculate-pi-dec",),
)
def main(n: int, seed: Optional[int] = None) -> float:
    """Calculate pi using the Monte Carlo method."""
    if n < 1:
        msg = "n must be greater than or equal to 1."
        logger.error(msg)
        raise ValueError(msg)
    logger.info(f"Calculating pi with {n} samples.")
    logger.debug(f"Seed: {seed}")

    random.seed(seed)
    xs = (random.random() for _ in range(n))  # noqa: S311
    ys = (random.random() for _ in range(n))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    pi_estimate = (4.0 * inside) / n

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))

    return pi_estimate


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pi_estimate = main(1_000_000)
    logger.info(f"Pi estimate: {pi_estimate}")
