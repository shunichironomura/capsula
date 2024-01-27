import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import orjson

import capsula
from capsula.context import FileContext, GitRepositoryContext
from capsula.encapsulator import Encapsulator
from capsula.reporter import JsonDumpReporter

logger = logging.getLogger(__name__)


@capsula.capsule(
    capsule_directory=Path(__file__).parents[1] / "vault" / datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S"),
    pre_run_contexts=(
        lambda capdir, _: FileContext(
            Path(__file__).parents[1] / "pyproject.toml",
            hash_algorithm="sha256",
            copy_to=capdir,
        ),
        GitRepositoryContext.default(),
    ),
    pre_run_reporters=(lambda capdir, _: JsonDumpReporter(capdir / "pre_run_report.json", option=orjson.OPT_INDENT_2),),
    in_run_watchers=(),
    post_run_contexts=(),
)
def calculate_pi(*, n_samples: int = 1_000, seed: int = 42) -> None:
    logger.info(f"Calculating pi with {n_samples} samples.")
    logger.debug(f"Seed: {seed}")
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))  # noqa: S311
    ys = (random.random() for _ in range(n_samples))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    enc.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    logger.info(f"Pi estimate: {pi_estimate}")
    enc.record("pi_estimate", pi_estimate)
    # raise CapsulaError("This is a test error.")

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    calculate_pi(1_000)
