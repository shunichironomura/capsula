import random
from pathlib import Path

import pytest

import capsula

OUTPUT_FILE_PATH = Path(__file__).parent / "pi.txt"


@capsula.run(ignore_config=True)
@capsula.context(capsula.CpuContext(), mode="pre")
@capsula.context(capsula.CwdContext(), mode="pre")
@capsula.context(capsula.EnvVarContext("PATH"), mode="pre")
@capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
@capsula.context(capsula.CommandContext.builder("uv export > requirements.txt"), mode="pre")
@capsula.context(capsula.CommandContext.builder("uv lock --locked"), mode="pre")
@capsula.context(capsula.GitRepositoryContext.builder("capsula"), mode="pre")
@capsula.context(capsula.FileContext.builder(Path(__file__).parents[1] / "requirements.txt", move=True), mode="pre")
@capsula.context(capsula.FileContext.builder(Path(__file__).parents[1] / "uv.lock", copy=True), mode="pre")
@capsula.context(capsula.FileContext.builder(Path(__file__).parents[1] / "pyproject.toml", copy=True), mode="pre")
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
@capsula.watcher(capsula.UncaughtExceptionWatcher("Exception"))
@capsula.context(capsula.FileContext.builder(OUTPUT_FILE_PATH, move=True), mode="post")
@capsula.reporter(capsula.JsonDumpReporter.builder(), mode="all")
@capsula.pass_pre_run_capsule
def calculate_pi(pre_run_capsule: capsula.Capsule, *, n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    capsula.record("pi_estimate", pi_estimate)

    with OUTPUT_FILE_PATH.open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}. Git SHA: {pre_run_capsule.data[('git', 'capsula')]['sha']}")


@pytest.mark.skip(reason="This test asserts very little, but contributes to most of the coverage.")
def test_decorator_e2e() -> None:
    calculate_pi(n_samples=10)
