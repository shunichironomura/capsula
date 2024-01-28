import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import orjson

import capsula
from capsula._context import FileContext, GitRepositoryContext
from capsula._reporter import JsonDumpReporter
from capsula._watcher import TimeWatcher
from capsula.encapsulator import Encapsulator

logger = logging.getLogger(__name__)


@capsula.run(
    capsule_directory=lambda: Path(__file__).parents[1]
    / "vault"
    / datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S"),
)
@capsula.context(
    lambda capdir, _: FileContext(
        Path(__file__).parents[1] / "pyproject.toml",
        hash_algorithm="sha256",
        copy_to=capdir,
    ),
    mode="pre",
)
@capsula.context(GitRepositoryContext.default(), mode="pre")
@capsula.reporter(
    lambda capdir, _, phase: JsonDumpReporter(capdir / f"{phase}-run-report.json", option=orjson.OPT_INDENT_2),
    mode="all",
)
@capsula.watcher(TimeWatcher("calculation_time"))
def calculate_pi(*, n_samples: int = 1_000, seed: int = 42) -> None:
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

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    calculate_pi(1_000)
