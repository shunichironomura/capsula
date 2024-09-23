import logging
import random
from pathlib import Path

from rich.logging import RichHandler

import capsula

logger = logging.getLogger(__name__)

PROJECT_ROOT = capsula.search_for_project_root(__file__)


@capsula.run(ignore_config=True, vault_dir=Path(__file__).parent / "vault")
@capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
@capsula.context(capsula.EnvVarContext("PATH"), mode="pre")
@capsula.context(capsula.CwdContext(), mode="pre")
@capsula.context(capsula.CpuContext(), mode="pre")
@capsula.context(capsula.GitRepositoryContext.builder("capsula"), mode="pre")
@capsula.context(capsula.CommandContext("uv lock --locked", cwd=PROJECT_ROOT), mode="pre")
@capsula.context(capsula.FileContext.builder(PROJECT_ROOT / "pyproject.toml", copy=True), mode="pre")
@capsula.context(capsula.FileContext.builder(PROJECT_ROOT / "uv.lock", copy=True), mode="pre")
@capsula.context(capsula.CommandContext("uv export > requirements.txt", cwd=PROJECT_ROOT), mode="pre")
@capsula.context(capsula.FileContext.builder(PROJECT_ROOT / "requirements.txt", move=True), mode="pre")
@capsula.watcher(capsula.UncaughtExceptionWatcher("Exception"))
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
@capsula.context(capsula.FileContext.builder("pi.txt", move=True), mode="post")
@capsula.reporter(capsula.JsonDumpReporter.builder(), mode="all")
@capsula.context(capsula.FunctionContext.builder(), mode="pre")
@capsula.pass_pre_run_capsule
def calculate_pi(pre_run_capsule: capsula.Capsule, *, n_samples: int = 1_000, seed: int = 42) -> None:
    logger.info(f"Calculating pi with {n_samples} samples.")
    logger.debug(f"Seed: {seed}")
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    logger.info(f"Pi estimate: {pi_estimate}")
    capsula.record("pi_estimate", pi_estimate)
    # raise CapsulaError("This is a test error.")
    logger.info(f"Run name: {capsula.current_run_name()}")

    with (Path("pi.txt")).open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}. Git SHA: {pre_run_capsule.data[('git', 'capsula')]['sha']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(show_time=False, show_path=True)],
    )
    calculate_pi(n_samples=1_000)
