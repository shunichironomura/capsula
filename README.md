# Capsula

[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/capsula.svg)](https://anaconda.org/conda-forge/capsula)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![Test Status](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![codecov](https://codecov.io/gh/shunichironomura/capsula/graph/badge.svg?token=BZXF2PPDM0)](https://codecov.io/gh/shunichironomura/capsula)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)

> [!NOTE]
> This project is still work in progress. Consider pinning the version to avoid breaking changes.

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of Capsula is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of past command execution, fostering reproducibility and consistency over time.

## Usage

1. **Context Capture:** Capsula logs the details of the execution context for future reference and reproduction. The context includes, but is not limited to, the Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring:** Capsula monitors the execution of a Python function, logging information such as the execution status, output, duration, etc.

3. **Context Diffing (to be implemented):** Capsula can compare the current context with the context captured at a previous point in time. This is useful for identifying changes or for reproducing the exact conditions of a past execution.

See the following Python script:

```python
import logging
import random
from pathlib import Path

import capsula

logger = logging.getLogger(__name__)


@capsula.run()
@capsula.reporter(capsula.JsonDumpReporter.default(), mode="all")
@capsula.context(capsula.FileContext.default(Path(__file__).parent / "pi.txt", move=True), mode="post")
@capsula.watcher(capsula.UncaughtExceptionWatcher("Exception"))
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "pyproject.toml", copy=True), mode="pre")
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "poetry.lock", copy=True), mode="pre")
@capsula.context(capsula.FileContext.default(Path(__file__).parents[1] / "requirements.txt", move=True), mode="pre")
@capsula.context(capsula.GitRepositoryContext.default(), mode="pre")
@capsula.context(capsula.CommandContext("poetry check --lock"), mode="pre")
@capsula.context(capsula.CommandContext("pip freeze --exclude-editable > requirements.txt"), mode="pre")
@capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
@capsula.context(capsula.EnvVarContext("PATH"), mode="pre")
@capsula.context(capsula.CwdContext(), mode="pre")
@capsula.context(capsula.CpuContext(), mode="pre")
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
    logger.info(pre_run_capsule.data)
    logger.info(capsula.current_run_name())

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}. Git SHA: {pre_run_capsule.data[('git', 'capsula')]['sha']}")


if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
```

- `@capsula.run` decorator specifies the directory where the execution context is stored. The directory is automatically created if it does not exist.
- `@capsula.context` decorator specifies the context to be captured. The context is captured before the execution of the decorated function if `mode` is `"pre"`, after the execution if `mode` is `"post"`, or both if `mode` is `"all"`.
- `@capsula.reporter` decorator specifies the reporter to be used. The reporter is called after the execution of the decorated function if `mode` is `"post"`, or both before and after the execution if `mode` is `"all"`.
- `@capsula.watcher` decorator specifies the watcher to be used during the execution of the decorated function.
- `capsula.record` function records the value of the specified variable. The value is stored in the execution context.

## Installation

You can install Capsula via pip:

```bash
pip install capsula
```
