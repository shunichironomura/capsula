import logging
import random
import sys
from pathlib import Path

from capsula import Encapsulator

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

# Set N_SAMPLES to 0 to raise an exception.
N_SAMPLES = 1_000_000
SEED = 0

# Create an encapsulator
pre_run_enc = Encapsulator()

# The order of the contexts is important.
pre_run_enc.add_context(("git", "capsula"), GitRepositoryContext(name="capsula", path=Path(__file__).parents[1]))
pre_run_enc.add_context("cpu", CpuInfoContext())
pre_run_enc.add_context("platform", PlatformContext())
pre_run_enc.add_context("cwd", CwdContext())
pre_run_enc.add_context(("env", "HOME"), EnvVarContext("HOME"))
pre_run_enc.add_context(EnvVarContext("PATH"))  # Default context name will be used
pre_run_enc.add_context(CommandContext("poetry lock --check"))
# This will have a side effect
pre_run_enc.add_context(CommandContext("pip freeze --exclude-editable > requirements.txt"))
pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "requirements.txt"), hash_algorithm="sha256", move=True)
pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "pyproject.toml"), hash_algorithm="sha256", copy=True)
pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "poetry.lock"), hash_algorithm="sha256", copy=True)

capsule = pre_run_enc.encapsulate()

# Actual calculation
in_run_enc = Encapsulator()

# Catch the exception raised by the encapsulated function.
in_run_enc.add_watcher(UncaughtExceptionWatcher(base=Exception, reraise=False))

# Record the time it takes to run the function.
in_run_enc.add_watcher(TimeWatcher(name="pi"))

with in_run_enc.watch():
    logger.info(f"Calculating pi with {N_SAMPLES} samples.")
    logger.debug(f"Seed: {SEED}")
    random.seed(SEED)
    xs = (random.random() for _ in range(N_SAMPLES))  # noqa: S311
    ys = (random.random() for _ in range(N_SAMPLES))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    pi_estimate = (4.0 * inside) / N_SAMPLES
    logger.info(f"Pi estimate: {pi_estimate}")

    with (Path(__file__).parent / "pi_cli.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))
