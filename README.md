# Capsula

[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/capsula.svg)](https://anaconda.org/conda-forge/capsula)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![Test Status](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![codecov](https://codecov.io/gh/shunichironomura/capsula/graph/badge.svg?token=BZXF2PPDM0)](https://codecov.io/gh/shunichironomura/capsula)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture their command/function execution context for reproducibility.
See the [documentation](https://shunichironomura.github.io/capsula/) for more information.

With Capsula, you can capture:

- CPU information with [`CpuContext`](docs/contexts/cpu.md)
- Python version with [`PlatformContext`](docs/contexts/platform.md)
- Current working directory with [`CwdContext`](docs/contexts/cwd.md)
- Git repository information (commit hash, branch, etc.) with [`GitRepositoryContext`](docs/contexts/git.md)
- Output of shell commands (e.g., `poetry check --lock`) with [`CommandContext`](docs/contexts/command.md)
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
    { type = "GitRepositoryContext", name = "capsula", path = ".", path_relative_to_project_root = true },
    { type = "CommandContext", command = "poetry check --lock", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "pyproject.toml", copy = true, path_relative_to_project_root = true },
    { type = "FileContext", path = "poetry.lock", copy = true, path_relative_to_project_root = true },
    { type = "CommandContext", command = "pip freeze --exclude-editable > requirements.txt", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "requirements.txt", move = true, path_relative_to_project_root = true },
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

After running the script, a directory (`calculate_pi_20240630_015823_S3vb` in this example) will be created under the `<project-root>/vault` directory, and you will find the following files there:

<details>
<summary>Example of output <code>pre-run-report.json</code>:</summary>
<pre><code>{
  "cwd": "/home/nomura/ghq/github.com/shunichironomura/capsula",
  "cpu": {
    "python_version": "3.8.17.final.0 (64 bit)",
    "cpuinfo_version": [
      9,
      0,
      0
    ],
    "cpuinfo_version_string": "9.0.0",
    "arch": "X86_64",
    "bits": 64,
    "count": 12,
    "arch_string_raw": "x86_64",
    "vendor_id_raw": "GenuineIntel",
    "brand_raw": "Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz",
    "hz_advertised_friendly": "2.9000 GHz",
    "hz_actual_friendly": "2.9040 GHz",
    "hz_advertised": [
      2900000000,
      0
    ],
    "hz_actual": [
      2904008000,
      0
    ],
    "stepping": 5,
    "model": 165,
    "family": 6,
    "flags": [
      "3dnowprefetch",
      "abm",
      "adx",
      "aes",
      "apic",
      "arch_capabilities",
      "arch_perfmon",
      "avx",
      "avx2",
      "bmi1",
      "bmi2",
      "clflush",
      "clflushopt",
      "cmov",
      "constant_tsc",
      "cpuid",
      "cx16",
      "cx8",
      "de",
      "ept",
      "ept_ad",
      "erms",
      "f16c",
      "flush_l1d",
      "fma",
      "fpu",
      "fsgsbase",
      "fxsr",
      "ht",
      "hypervisor",
      "ibpb",
      "ibrs",
      "ibrs_enhanced",
      "invpcid",
      "invpcid_single",
      "lahf_lm",
      "lm",
      "mca",
      "mce",
      "md_clear",
      "mmx",
      "movbe",
      "msr",
      "mtrr",
      "nopl",
      "nx",
      "osxsave",
      "pae",
      "pat",
      "pcid",
      "pclmulqdq",
      "pdcm",
      "pdpe1gb",
      "pge",
      "pni",
      "popcnt",
      "pse",
      "pse36",
      "rdrand",
      "rdrnd",
      "rdseed",
      "rdtscp",
      "rep_good",
      "sep",
      "smap",
      "smep",
      "ss",
      "ssbd",
      "sse",
      "sse2",
      "sse4_1",
      "sse4_2",
      "ssse3",
      "stibp",
      "syscall",
      "tpr_shadow",
      "tsc",
      "vme",
      "vmx",
      "vnmi",
      "vpid",
      "x2apic",
      "xgetbv1",
      "xsave",
      "xsavec",
      "xsaveopt",
      "xsaves",
      "xtopology"
    ],
    "l3_cache_size": 12582912,
    "l2_cache_size": "1.5 MiB",
    "l1_data_cache_size": 196608,
    "l1_instruction_cache_size": 196608,
    "l2_cache_line_size": 256,
    "l2_cache_associativity": 6
  },
  "git": {
    "capsula": {
      "working_dir": "/home/nomura/ghq/github.com/shunichironomura/capsula",
      "sha": "db7b86d3ed95e178521cd140505f1c8b25f4f30e",
      "remotes": {
        "origin": "ssh://git@github.com/shunichironomura/capsula.git"
      },
      "branch": "update-readme",
      "is_dirty": false
    }
  },
  "command": {
    "poetry check --lock": {
      "command": "poetry check --lock",
      "cwd": null,
      "returncode": 0,
      "stdout": "All set!\n",
      "stderr": ""
    },
    "pip freeze --exclude-editable > requirements.txt": {
      "command": "pip freeze --exclude-editable > requirements.txt",
      "cwd": null,
      "returncode": 0,
      "stdout": "",
      "stderr": ""
    }
  },
  "file": {
    "pyproject.toml": {
      "copied_to": [
        "vault/calculate_pi_20240630_015823_S3vb/pyproject.toml"
      ],
      "moved_to": null,
      "hash": {
        "algorithm": "sha256",
        "digest": "9b2ccc978e950a3a4d2b5f3d29eadab593e1ffe8cd48e7606389e214cb82c8a6"
      }
    },
    "poetry.lock": {
      "copied_to": [
        "vault/calculate_pi_20240630_015823_S3vb/poetry.lock"
      ],
      "moved_to": null,
      "hash": {
        "algorithm": "sha256",
        "digest": "8d89f9943c8e515340a5c8c16b17a30a749d935ffe765024acaaa81fc1ed5587"
      }
    },
    "requirements.txt": {
      "copied_to": [],
      "moved_to": "vault/calculate_pi_20240630_015823_S3vb",
      "hash": {
        "algorithm": "sha256",
        "digest": "b7a36d48fda3efc9374d7d8b0fd4d910234497e2cf229001a1c2c76fce35810c"
      }
    }
  }
}</code></pre>
</details>

<details>
<summary>Example of output <code>in-run-report.json</code>:</summary>
<pre><code>{
  "function": {
    "calculate_pi": {
      "file_path": "examples/simple_decorator.py",
      "first_line_no": 6,
      "args": [],
      "kwargs": {
        "n_samples": 1000
      }
    }
  },
  "inside": 782,
  "pi_estimate": 3.128,
  "time": {
    "execution_time": "0:00:00.000568"
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
      "moved_to": "vault/calculate_pi_20240630_015823_S3vb",
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
