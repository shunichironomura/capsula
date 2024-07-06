import random
from pathlib import Path

import capsula

OUTPUT_FILE_PATH = Path(__file__).parent / "pi.txt"


@capsula.run(ignore_config=True)
@capsula.context(capsula.CpuContext(), mode="pre")
@capsula.context(capsula.CwdContext(), mode="pre")
@capsula.context(capsula.EnvVarContext("PATH"), mode="pre")
@capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
@capsula.context(capsula.CommandContext.default("pip freeze --exclude-editable > requirements.txt"), mode="pre")
@capsula.context(capsula.CommandContext.default("poetry check --lock"), mode="pre")
@capsula.context(capsula.GitRepositoryContext.default("capsula"), mode="pre")
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "requirements.txt", move=True), mode="pre")
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "poetry.lock", copy=True), mode="pre")
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "pyproject.toml", copy=True), mode="pre")
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
@capsula.watcher(capsula.UncaughtExceptionWatcher("Exception"))
@capsula.context(capsula.FileContext.default(OUTPUT_FILE_PATH, move=True), mode="post")
@capsula.reporter(capsula.JsonDumpReporter.default(), mode="all")
@capsula.pass_pre_run_capsule
def calculate_pi(pre_run_capsule: capsula.Capsule, *, n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))  # noqa: S311
    ys = (random.random() for _ in range(n_samples))  # noqa: S311
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    capsula.record("pi_estimate", pi_estimate)

    with OUTPUT_FILE_PATH.open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}. Git SHA: {pre_run_capsule.data[('git', 'capsula')]['sha']}")


def test_decorator_e2e() -> None:
    calculate_pi(n_samples=10)
