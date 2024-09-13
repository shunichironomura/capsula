import logging
import random
from datetime import datetime, timezone
from pathlib import Path

import orjson

import capsula

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

N_SAMPLES = 1_000
SEED = 0


# Define the run name and create the capsule directory
run_name = datetime.now(timezone.utc).astimezone().strftime(r"%Y%m%d_%H%M%S")
capsule_directory = Path(__file__).parents[1] / "vault" / run_name
capsule_directory.mkdir(parents=True, exist_ok=True)

# Create an encapsulator
pre_run_enc = capsula.Encapsulator()

# Create a reporter
pre_run_reporter = capsula.JsonDumpReporter(capsule_directory / "pre_run_report.json", option=orjson.OPT_INDENT_2)
# slack_reporter = SlackReporter(
#     webhook_url="https://hooks.slack.com/services/T01JZQZQZQZ/B01JZQZQZQZ/QQZQZQZQZQZQZQZQZQZQZQZ",
#     channel="test",
#     username="test",
# )

# The order of the contexts is important.
pre_run_enc.record("run_name", run_name)
pre_run_enc.add_context(
    capsula.GitRepositoryContext(
        name="capsula",
        path=Path(__file__).parents[1],
        diff_file=capsule_directory / "capsula.diff",
        allow_dirty=True,
    ),
    key=("git", "capsula"),
)
pre_run_enc.add_context(capsula.CpuContext())
pre_run_enc.add_context(capsula.PlatformContext())
pre_run_enc.add_context(capsula.CwdContext())
pre_run_enc.add_context(capsula.EnvVarContext("HOME"), key=("env", "HOME"))
pre_run_enc.add_context(capsula.EnvVarContext("PATH"))  # Default key will be used
pre_run_enc.add_context(capsula.CommandContext("uv lock --locked"))
# This will have a side effect
pre_run_enc.add_context(capsula.CommandContext("pip freeze --exclude-editable > requirements.txt"))
pre_run_enc.add_context(
    capsula.FileContext(
        Path(__file__).parents[1] / "requirements.txt",
        hash_algorithm="sha256",
        move_to=capsule_directory,
    ),
)
pre_run_enc.add_context(
    capsula.FileContext(
        Path(__file__).parents[1] / "pyproject.toml",
        hash_algorithm="sha256",
        copy_to=capsule_directory,
    ),
)
pre_run_enc.add_context(
    capsula.FileContext(Path(__file__).parents[1] / "uv.lock", hash_algorithm="sha256", copy_to=capsule_directory),
)

pre_run_capsule = pre_run_enc.encapsulate()
pre_run_reporter.report(pre_run_capsule)
# slack_reporter.report(pre_run_capsule)

# Actual calculation
in_run_enc = capsula.Encapsulator()
in_run_reporter = capsula.JsonDumpReporter(capsule_directory / "in_run_report.json", option=orjson.OPT_INDENT_2)

# The order matters. The first watcher will be the innermost one.
# Record the time it takes to run the function.
in_run_enc.add_watcher(capsula.TimeWatcher("calculation_time"))

# Catch the exception raised by the encapsulated function.
in_run_enc.add_watcher(capsula.UncaughtExceptionWatcher("Exception", base=Exception))

with in_run_enc.watch():
    logger.info(f"Calculating pi with {N_SAMPLES} samples.")
    logger.debug(f"Seed: {SEED}")
    random.seed(SEED)
    xs = (random.random() for _ in range(N_SAMPLES))
    ys = (random.random() for _ in range(N_SAMPLES))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    in_run_enc.record("inside", inside)

    pi_estimate = (4.0 * inside) / N_SAMPLES
    logger.info(f"Pi estimate: {pi_estimate}")
    in_run_enc.record("pi_estimate", pi_estimate)
    # raise CapsulaError("This is a test error.")

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))

in_run_enc.add_context(
    capsula.FileContext(Path(__file__).parent / "pi.txt", hash_algorithm="sha256", move_to=capsule_directory),
)

in_run_capsule = in_run_enc.encapsulate()
in_run_reporter.report(in_run_capsule)
# slack_reporter.report(in_run_capsule)
