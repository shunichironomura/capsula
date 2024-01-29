# Capsula

![Test Status](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)
![Coverage Status](coverage/badge.svg?dummy=8484744)

> [!NOTE]
> This project is still work in progress. Consider pinning the version to avoid breaking changes.

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of Capsula is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of past command execution, fostering reproducibility and consistency over time.

## Usage

1. **Context Capture:** Capsula logs the details of the execution context for future reference and reproduction. The context includes, but is not limited to, the Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring:** Capsula monitors the execution of Python scripts and CLI commands, logging information such as the execution status, output, duration, etc.

3. **Context Reproduction (to be implemented):** Capsula enables the reproduction of the captured context. This ensures the consistency and reproducibility of results.

See the following Python script:

```python
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

import orjson

import capsula

logger = logging.getLogger(__name__)


@capsula.run(
    run_dir=lambda _: Path(__file__).parents[1] / "vault" / datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S"),
)
@capsula.context(
    lambda params: capsula.FileContext(
        Path(__file__).parents[1] / "pyproject.toml",
        hash_algorithm="sha256",
        copy_to=params.run_dir,
    ),
    mode="pre",
)
@capsula.context(capsula.GitRepositoryContext.default(), mode="pre")
@capsula.reporter(
    lambda params: capsula.JsonDumpReporter(
        params.run_dir / f"{params.phase}-run-report.json",
        option=orjson.OPT_INDENT_2,
    ),
    mode="all",
)
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
@capsula.context(
    lambda params: capsula.FileContext(
        Path(__file__).parent / "pi.txt",
        hash_algorithm="sha256",
        move_to=params.run_dir,
    ),
    mode="post",
)
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

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(str(pi_estimate))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
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
