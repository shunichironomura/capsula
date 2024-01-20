import logging
import random
from datetime import UTC, datetime
from pathlib import Path

from capsula import Encapsulator
from capsula.context import CwdContext
from capsula.reporter import JsonDumpReporter

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

# Set N_SAMPLES to 0 to raise an exception.
N_SAMPLES = 1_000_000
SEED = 0

# Define the run name and create the capsule directory
run_name = datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S")
capsule_directory = Path(__file__).parents[1] / "vault" / run_name
capsule_directory.mkdir(parents=True, exist_ok=True)

# Create an encapsulator
pre_run_enc = Encapsulator()

# Create a reporter
pre_run_reporter = JsonDumpReporter(capsule_directory / "pre_run_report.json")
# slack_reporter = SlackReporter(
#     webhook_url="https://hooks.slack.com/services/T01JZQZQZQZ/B01JZQZQZQZ/QQZQZQZQZQZQZQZQZQZQZQZ",
#     channel="test",
#     username="test",
# )

# The order of the contexts is important.
pre_run_enc.record("run_name", run_name)
# pre_run_enc.add_context(GitRepositoryContext(name="capsula", path=Path(__file__).parents[1]), key=("git", "capsula"))
# pre_run_enc.add_context(CpuInfoContext(), key="cpu")
# pre_run_enc.add_context(PlatformContext(), key="platform")
pre_run_enc.add_context(CwdContext(), key="cwd")
# pre_run_enc.add_context(EnvVarContext("HOME"), key=("env", "HOME"))
# pre_run_enc.add_context(EnvVarContext("PATH"))  # Default key will be used
# pre_run_enc.add_context(CommandContext("poetry lock --check"))
# # This will have a side effect
# pre_run_enc.add_context(CommandContext("pip freeze --exclude-editable > requirements.txt"))
# pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "requirements.txt"), hash_algorithm="sha256", move=True)
# pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "pyproject.toml"), hash_algorithm="sha256", copy=True)
# pre_run_enc.add_context(FlieContext(Path(__file__).parents[1] / "poetry.lock"), hash_algorithm="sha256", copy=True)

pre_run_capsule = pre_run_enc.encapsulate()
pre_run_reporter.report(pre_run_capsule)
# slack_reporter.report(pre_run_capsule)

# Actual calculation
in_run_enc = Encapsulator()
in_run_reporter = JsonDumpReporter(capsule_directory / "in_run_report.json")

# The order matters. The first watcher will be the innermost.
# Record the time it takes to run the function.
# in_run_enc.add_watcher(TimeWatcher(name="pi"))

# Catch the exception raised by the encapsulated function.
# in_run_enc.add_watcher(UncaughtExceptionWatcher(base=Exception, reraise=False))

with in_run_enc:
    logger.info(f"Calculating pi with {N_SAMPLES} samples.")
    logger.debug(f"Seed: {SEED}")
    random.seed(SEED)
    xs = (random.random() for _ in range(N_SAMPLES))  # noqa: S311
    ys = (random.random() for _ in range(N_SAMPLES))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    in_run_enc.record("inside", inside)

    pi_estimate = (4.0 * inside) / N_SAMPLES
    logger.info(f"Pi estimate: {pi_estimate}")

    with (Path(__file__).parent / "pi_cli.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))

# in_run_enc.add_context(FileContext(Path(__file__).parent / "pi.txt", hash_algorithm="sha256", move=True))

in_run_capsule = in_run_enc.encapsulate()
in_run_reporter.report(in_run_capsule)
# slack_reporter.report(in_run_capsule)
