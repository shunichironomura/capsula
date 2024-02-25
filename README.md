# Capsula

[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/capsula.svg)](https://anaconda.org/conda-forge/capsula)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![Test Status](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![codecov](https://codecov.io/gh/shunichironomura/capsula/graph/badge.svg?token=BZXF2PPDM0)](https://codecov.io/gh/shunichironomura/capsula)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of Capsula is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of past command execution, fostering reproducibility and consistency over time.

Features:

1. **Context Capture:** Capsula logs the details of the execution context for future reference and reproduction. The context includes, but is not limited to, the Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring:** Capsula monitors the execution of a Python function, logging information such as the execution status, output, duration, etc.

3. **Context Diffing (to be implemented):** Capsula can compare the current context with the context captured at a previous point in time. This is useful for identifying changes or for reproducing the exact conditions of a past execution.

## Usage

Prepare a `capsula.toml` file in the root directory of your project. An example of the `capsula.toml` file is as follows:

```toml
[pre-run]
# Contexts to be captured before the execution of the decorated function/CLI command.
contexts = [
    { type = "CommandContext", command = "poetry check --lock" },
    { type = "CommandContext", command = "pip freeze --exclude-editable > requirements.txt" },
    { type = "FileContext", path = "pyproject.toml", copy = true },
    { type = "FileContext", path = "requirements.txt", move = true },
    { type = "GitRepositoryContext", name = "capsula" },
    { type = "CwdContext" },
    { type = "CpuContext" },
]
# Reporter to be used to report the captured contexts.
reporters = [{ type = "JsonDumpReporter" }]

[in-run]
# Watchers to be used during the execution of the decorated function/CLI command.
watchers = [{ type = "UncaughtExceptionWatcher" }, { type = "TimeWatcher" }]
# Reporter to be used to report the execution status.
reporters = [{ type = "JsonDumpReporter" }]

[post-run]
# Contexts to be captured after the execution of the decorated function/CLI command.
contexts = [{ type = "FileContext", path = "examples/pi.txt", move = true }]
# Reporter to be used to report the captured contexts.
reporters = [{ type = "JsonDumpReporter" }]
```

Then, all you need to do is decorate your Python function with the `@capsula.run` decorator and specify the `load_from_config` argument as `True`. The following is an example of a Python script that estimates the value of π using the Monte Carlo method:

```python
import random
from pathlib import Path

import capsula

@capsula.run(load_from_config=True)
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

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")

if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
```

<details>
<summary>Example of output <code>pre-run-report.json</code>:</summary>
<pre><code>{
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
        "vault/calculate_pi_20240225_221901_M7b3/pyproject.toml"
      ],
      "moved_to": null,
      "hash": {
        "algorithm": "sha256",
        "digest": "6c59362587bf43411461b69675980ea338d83a468acddbc8f6cac4f2c17f7605"
      }
    },
    "requirements.txt": {
      "copied_to": [],
      "moved_to": "vault/calculate_pi_20240225_221901_M7b3",
      "hash": {
        "algorithm": "sha256",
        "digest": "99d0dbddd7f27aa25bd2d7ce3e2f4a555cdb48b039d73a6cf01fc5fa33f527e1"
      }
    }
  },
  "git": {
    "capsula": {
      "working_dir": "/home/nomura/ghq/github.com/shunichironomura/capsula",
      "sha": "ff51cb6245e43253d036fcaa0b2af09c0089b783",
      "remotes": {
        "origin": "ssh://git@github.com/shunichironomura/capsula.git"
      },
      "branch": "improve-example",
      "is_dirty": true
    }
  },
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
      2904010000,
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
  }
}</code></pre>
</details>

<details>
<summary>Example of output <code>in-run-report.json</code>:</summary>
<pre><code>{
  "function": {
    "calculate_pi": {
      "file_path": "examples/simple_decorator.py",
      "first_line_no": 10,
      "args": [],
      "kwargs": {
        "n_samples": 1000
      }
    }
  },
  "inside": 782,
  "pi_estimate": 3.128,
  "exception": {
    "exception": {
      "exc_type": null,
      "exc_value": null,
      "traceback": null
    }
  },
  "time": {
    "execution_time": "0:00:00.000658"
  }
}</code></pre>
</details>

<details>
<summary>Example of output <code>post-run-report.json</code>:</summary>
<pre><code>{
  "file": {
    "examples/pi.txt": {
      "copied_to": [],
      "moved_to": "vault/calculate_pi_20240225_221901_M7b3",
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
