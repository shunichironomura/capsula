import logging
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

    return 3.1415926535897932384626433832795028841971


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(1_000_000)
