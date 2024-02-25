import logging
import random
from pathlib import Path

from rich.logging import RichHandler

import capsula

logger = logging.getLogger(__name__)


@capsula.run(load_from_config=True)
@capsula.pass_pre_run_capsule
def calculate_pi(pre_run_capsule: capsula.Capsule, *, n_samples: int = 1_000, seed: int = 42) -> None:
    logger.info(f"Calculating pi with {n_samples} samples.")
    logger.debug(f"Seed: {seed}")
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))  # noqa: S311
    ys = (random.random() for _ in range(n_samples))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    logger.info(f"Pi estimate: {pi_estimate}")
    capsula.record("pi_estimate", pi_estimate)
    # raise CapsulaError("This is a test error.")
    logger.info(f"Run name: {capsula.current_run_name()}")

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}. Git SHA: {pre_run_capsule.data[('git', 'capsula')]['sha']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(show_time=False, show_path=True)],
    )
    calculate_pi(n_samples=1_000)
