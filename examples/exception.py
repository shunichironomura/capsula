import logging
from pathlib import Path

import capsula

logger = logging.getLogger(__name__)


@capsula.monitor(
    directory=Path(__file__).parents[1],
    include_return_value=True,
)
def divide_by_zero(x: float) -> float:
    return x / 0.0


if __name__ == "__main__":
    divide_by_zero(1.0)
