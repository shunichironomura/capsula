import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import orjson

import capsula

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


def calc_pi(n_samples: int, seed: int) -> float:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))  # noqa: S311
    ys = (random.random() for _ in range(n_samples))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    logger.info(f"Pi estimate: {pi_estimate}")
    capsula.record("pi_estimate", pi_estimate)

    return pi_estimate


def main(n_samples: int, seed: int) -> None:
    # Define the run name and create the capsule directory
    run_name = datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S")
    capsule_directory = Path(__file__).parents[1] / "vault" / run_name

    with capsula.Run() as run:
        logger.info(f"Calculating pi with {n_samples} samples.")
        logger.debug(f"Seed: {seed}")

        pi_estimate = calc_pi(n_samples, seed)

        with (Path(__file__).parent / "pi.txt").open("w") as output_file:
            output_file.write(str(pi_estimate))

    in_run_capsule = run.encapsulate()

    in_run_reporter = capsula.JsonDumpReporter(capsule_directory / "in_run_report.json", option=orjson.OPT_INDENT_2)
    in_run_reporter.report(in_run_capsule)


if __name__ == "__main__":
    main(1000, 42)
