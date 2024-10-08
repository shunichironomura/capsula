# Capsula

[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/capsula.svg)](https://anaconda.org/conda-forge/capsula)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![Test Status](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![codecov](https://codecov.io/gh/shunichironomura/capsula/graph/badge.svg?token=BZXF2PPDM0)](https://codecov.io/gh/shunichironomura/capsula)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture their command/function execution context for reproducibility.
See the [documentation](https://shunichironomura.github.io/capsula/) for more information.

With Capsula, you can capture:

- CPU information with [`CpuContext`](docs/contexts/cpu.md)
- Python version with [`PlatformContext`](docs/contexts/platform.md)
- Current working directory with [`CwdContext`](docs/contexts/cwd.md)
- Git repository information (commit hash, branch, etc.) with [`GitRepositoryContext`](docs/contexts/git.md)
- Output of shell commands (e.g., `uv lock --locked`) with [`CommandContext`](docs/contexts/command.md)
- Files (e.g., output files, `pyproject.toml`, `requirements.txt`) with [`FileContext`](docs/contexts/file.md)
- Arguments of Python functions with [`FunctionContext`](docs/contexts/function.md)
- Environment variables with [`EnvVarContext`](docs/contexts/envvar.md)
- Uncaught exceptions with [`UncaughtExceptionWatcher`](docs/watchers/uncaught_exception.md)
- Execution time with [`TimeWatcher`](docs/watchers/time.md)

The captured contexts are dumped into JSON files for future reference and reproduction.

## Usage example

For project-wide settings, prepare a `capsula.toml` file in the root directory of your project. An example of the `capsula.toml` file is as follows:

```toml
[pre-run]
contexts = [
    { type = "CwdContext" },
    { type = "CpuContext" },
    { type = "PlatformContext" },
    { type = "GitRepositoryContext", name = "capsula", path = ".", path_relative_to_project_root = true },
    { type = "CommandContext", command = "uv lock --locked", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "pyproject.toml", copy = true, path_relative_to_project_root = true },
    { type = "FileContext", path = "uv.lock", copy = true, path_relative_to_project_root = true },
    { type = "CommandContext", command = "uv export > requirements.txt", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "requirements.txt", move = true, path_relative_to_project_root = true },
    { type = "EnvVarContext", name = "HOME" },
]
reporters = [{ type = "JsonDumpReporter" }]

[in-run]
watchers = [{ type = "UncaughtExceptionWatcher" }, { type = "TimeWatcher" }]
reporters = [{ type = "JsonDumpReporter" }]

[post-run]
reporters = [{ type = "JsonDumpReporter" }]
```

Then, all you need to do is decorate your Python function with the `@capsula.run()` decorator. You can also use the `@capsula.context()` decorator to add a context specific to the function.

The following is an example of a Python script that estimates the value of π using the Monte Carlo method:

```python
import random
import capsula

@capsula.run()
@capsula.context(capsula.FunctionContext.builder(), mode="pre")
@capsula.context(capsula.FileContext.builder("pi.txt", move=True), mode="post")
def calculate_pi(n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    # You can record values to the capsule using the `record` method.
    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    print(f"Pi estimate: {pi_estimate}")
    capsula.record("pi_estimate", pi_estimate)
    print(f"Run name: {capsula.current_run_name()}")

    with open("pi.txt", "w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")

if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
```

After running the script, a directory (`calculate_pi_20240913_194900_2lxL` in this example) will be created under the `<project-root>/vault` directory, and you will find the output files in the directory:

```bash
$ tree vault/calculate_pi_20240913_194900_2lxL
vault/calculate_pi_20240913_194900_2lxL
├── in-run-report.json    # Generated by the `JsonDumpReporter` in `capsula.toml` (`in-run` section)
├── pi.txt                # Moved by the `FileContext` specified with the decorator in the script
├── uv.lock           # Copied by the `FileContext` specified in `capsula.toml` (`pre-run` section)
├── post-run-report.json  # Generated by the `JsonDumpReporter` in `capsula.toml` (`post-run` section)
├── pre-run-report.json   # Generated by the `JsonDumpReporter` in `capsula.toml` (`pre-run` section)
├── pyproject.toml        # Copied by the `FileContext` specified in `capsula.toml` (`pre-run` section)
└── requirements.txt      # Moved by the `FileContext` specified in `capsula.toml` (`pre-run` section)
```

The contents of the JSON files are as follows:

<details>
<summary>Example of output <code>pre-run-report.json</code>:</summary>
<pre><code>{
  "cwd": "/Users/nomura/ghq/github.com/shunichironomura/capsula",
  "cpu": {
    "python_version": "3.8.20.final.0 (64 bit)",
    "cpuinfo_version": [
      9,
      0,
      0
    ],
    "cpuinfo_version_string": "9.0.0",
    "arch": "ARM_8",
    "bits": 64,
    "count": 16,
    "arch_string_raw": "arm64",
    "brand_raw": "Apple M3 Max"
  },
  "platform": {
    "machine": "arm64",
    "node": "MacBook-Pro.local",
    "platform": "macOS-14.6.1-arm64-arm-64bit",
    "release": "23.6.0",
    "version": "Darwin Kernel Version 23.6.0: Mon Jul 29 21:14:46 PDT 2024; root:xnu-10063.141.2~1/RELEASE_ARM64_T6031",
    "system": "Darwin",
    "processor": "arm",
    "python": {
      "executable_architecture": {
        "bits": "64bit",
        "linkage": ""
      },
      "build_no": "default",
      "build_date": "Sep  9 2024 22:25:40",
      "compiler": "Clang 18.1.8 ",
      "branch": "",
      "implementation": "CPython",
      "version": "3.8.20"
    }
  },
  "git": {
    "capsula": {
      "working_dir": "/Users/nomura/ghq/github.com/shunichironomura/capsula",
      "sha": "4ff5b9b9e5f6b527b0c2c660a5cb1a12937599b5",
      "remotes": {
        "origin": "ssh://git@github.com/shunichironomura/capsula.git"
      },
      "branch": "gitbutler/workspace",
      "is_dirty": true,
      "diff_file": "/Users/nomura/ghq/github.com/shunichironomura/capsula/vault/calculate_pi_20240913_194900_2lxL/capsula.diff"
    }
  },
  "command": {
    "uv lock --locked": {
      "command": "uv lock --locked",
      "cwd": "/Users/nomura/ghq/github.com/shunichironomura/capsula",
      "returncode": 0,
      "stdout": "",
      "stderr": "Resolved 73 packages in 0.35ms\n"
    },
    "uv export > requirements.txt": {
      "command": "uv export > requirements.txt",
      "cwd": "/Users/nomura/ghq/github.com/shunichironomura/capsula",
      "returncode": 0,
      "stdout": "",
      "stderr": "Resolved 73 packages in 0.32ms\n"
    }
  },
  "file": {
    "/Users/nomura/ghq/github.com/shunichironomura/capsula/pyproject.toml": {
      "copied_to": [
        "/Users/nomura/ghq/github.com/shunichironomura/capsula/vault/calculate_pi_20240913_194900_2lxL/pyproject.toml"
      ],
      "moved_to": null,
      "hash": {
        "algorithm": "sha256",
        "digest": "e331c7998167d64e4e90c9f2aa2c2fe9c9c3afe1cf8348f1d61998042b75040a"
      }
    },
    "/Users/nomura/ghq/github.com/shunichironomura/capsula/uv.lock": {
      "copied_to": [
        "/Users/nomura/ghq/github.com/shunichironomura/capsula/vault/calculate_pi_20240913_194900_2lxL/uv.lock"
      ],
      "moved_to": null,
      "hash": {
        "algorithm": "sha256",
        "digest": "62e5b7a5125778dd664ee2dc0cb3c10640d15db3e55b40240c4d652f8afe40fe"
      }
    },
    "/Users/nomura/ghq/github.com/shunichironomura/capsula/requirements.txt": {
      "copied_to": [],
      "moved_to": "/Users/nomura/ghq/github.com/shunichironomura/capsula/vault/calculate_pi_20240913_194900_2lxL",
      "hash": {
        "algorithm": "sha256",
        "digest": "3ba457abcefb0010a7b350e8a2567b8ac890726608b99ce85defbb5d06e197de"
      }
    }
  },
  "env": {
    "HOME": "/Users/nomura"
  },
  "function": {
    "calculate_pi": {
      "file_path": "examples/simple_decorator.py",
      "first_line_no": 15,
      "bound_args": {
        "n_samples": 1000,
        "seed": 42
      }
    }
  }
}</code></pre>
</details>

<details>
<summary>Example of output <code>in-run-report.json</code>:</summary>
<pre><code>{
  "inside": 782,
  "pi_estimate": 3.128,
  "time": {
    "execution_time": "0:00:00.000271"
  },
  "exception": {
    "exception": {
      "exc_type": null,
      "exc_value": null,
      "traceback": null
    }
  }
}</code></pre>
</details>

<details>
<summary>Example of output <code>post-run-report.json</code>:</summary>
<pre><code>{
  "file": {
    "pi.txt": {
      "copied_to": [],
      "moved_to": "/Users/nomura/ghq/github.com/shunichironomura/capsula/vault/calculate_pi_20240913_194900_2lxL",
      "hash": {
        "algorithm": "sha256",
        "digest": "a64c761cb6b6f9ef1bc1f6afa6ba44d796c5c51d14df0bdc9d3ab9ced7982a74"
      }
    }
  }
}</code></pre>
</details>

## Installation

You can install Capsula via pip:

```bash
pip install capsula
```

Or via conda:

```bash
conda install conda-forge::capsula
```

## Licensing

This project is licensed under the terms of the MIT.

Additionally, this project includes code derived from the Python programming language, which is licensed under the Python Software Foundation License Version 2 (PSF-2.0). For details, see the LICENSE file.
