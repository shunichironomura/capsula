# Capsula

![Test Statue](https://github.com/shunichironomura/capsula/workflows/Test/badge.svg?event=push&branch=main)
[![PyPI](https://img.shields.io/pypi/v/capsula)](https://pypi.org/project/capsula/)
![PyPI - License](https://img.shields.io/pypi/l/capsula)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/capsula)
![PyPI - Downloads](https://img.shields.io/pypi/dm/capsula)
![Coverage Status](reports/coverage/badge.svg?dummy=8484744)

> ⚠️ **NOTE**: This project is still work in progress. Consider pinning the version to avoid breaking changes.

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of Capsula is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of a past command execution, fostering reproducibility and consistency over time.

## Usage

1. **Context Capture:** Capsula logs the details of the execution context for future reference and reproduction. The context includes, but not limited to, Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring:** Capsula monitors the execution of Python scripts and CLI commands, logging information such as the execution status, output, duration, etc.

3. **Context Reproduction (to be implemented):** Capsula enables the reproduction of the captured context. This ensures the consistency and reproducibility of results.

## Setup

### Installation

You can install Capsula via pip:

```bash
pip install capsula
```

### Configuration

At the root of your project, create a `capsula.toml` file. The following is an example of a `capsula.toml` file. Note that the root directory is the directory where `capsula.toml` is located.

```toml
# The directory where the captured context is stored.
vault-directory = 'vault'

# The template for the capsule directory name.
# It will be formatted by `datetime.now(UTC).astimezone().strftime(capsule_template)`.
capsule-template = '%Y%m%d_%H%M%S'

[capture]
# Whether to include CPU information in the captured context.
# Note that this may take a relatively long time to capture.
include-cpu = true

# List of commands to run before capturing the context.
# They are executed in the order specified, and if one of them fails, the subsequent commands are not executed.
# The commands are executed in the root directory.
pre-capture-commands = [
    'poetry lock --check',
    'pip freeze --exclude-editable > requirements.txt',
]

# List of environment variables to include in the captured context.
environment-variables = [
    'HOME',
]

[capture.files]
# List of files (relative to the root directory) to include in the captured context.
# If `hash` is specified, the file hash computed with the specified algorithm will be included in the captured context.
# If `move` is set to true, the file will be moved to the vault directory. (default: false)
# If `copy` is set to true, the file will be copied to the vault directory. (default: false)
# You cannot set both `move` and `copy` to true.
"pyproject.toml" = { hash = "sha256", copy = true }
"poetry.lock" = { hash = "sha256", copy = true }
"requirements.txt" = { hash = "sha256", move = true }

[capture.git.repositories]
# Git repositories to include in the captured context, relative to the root directory.
"repository-name" = '.'

[monitor]
# Whether to capture the context before running the command using the `capture` configuration.
capture = true

# You can configure the monitoring behavior for each "item" (e.g., Python function, CLI command).
[monitor.item.calculate-pi-cli.files]
# List of files (relative to the root directory) to include after the execution of the command.
"examples/pi_cli.png" = { hash = "sha256", move = true }

[monitor.item.calculate-pi-dec.files]
"examples/pi_dec.png" = { hash = "sha256", move = true }
```


## Usage

### Context Capture

Running `capsula capture` outputs the following files in the capsule directory:

- `context.json`: The captured context.
- `<repo-name>.diff`: The diff of the Git repository.
- Files specified with either `copy = true` or `move = true` in `capsula.toml`.

<details>
<summary>Example of <code>context.json</code></summary>

```json
{
    "root_directory": "/path/to/root/directory",
    "cwd": "/path/to/current/working/directory",
    "platform": {
        "machine": "x86_64",
        "node": "DESKTOP-XXXXXX",
        "platform": "Linux-5.15.90.1-microsoft-standard-WSL2-x86_64-with-glibc2.35",
        "release": "5.15.90.1-microsoft-standard-WSL2",
        "version": "#1 SMP Fri Jan 27 02:56:13 UTC 2023",
        "system": "Linux",
        "processor": "x86_64",
        "python": {
            "executable_architecture": {
                "bits": "64bit",
                "linkage": "ELF"
            },
            "build_no": "main",
            "build_date": "Dec 30 2022 17:24:31",
            "compiler": "GCC 9.4.0",
            "branch": "",
            "implementation": "CPython",
            "version": "3.11.1"
        }
    },
    "environment_variables": {
        "HOME": "/home/user"
    },
    "git": {
        "capsula": {
            "path": ".",
            "sha": "ebc5b7053733453ca344af28b42fa3f6d5e0d619",
            "branch": "main",
            "remotes": [
                {
                    "name": "origin",
                    "url": "git@github.com:shunichironomura/capsula.git"
                }
            ]
        }
    },
    "files": {
        "pyproject.toml": {
            "hash_algorithm": "sha256",
            "file_hash": "b4b638c3b8212210f4cfc1e34bab0467ede487b44dbc9cedbe76602221a93b99"
        },
        "poetry.lock": {
            "hash_algorithm": "sha256",
            "file_hash": "64c2919133d0f6f1e74463d97be6f98c90a085670106451747a5062aae1fff08"
        },
        "requirements.txt": {
            "hash_algorithm": "sha256",
            "file_hash": "73c60f406d08aa3d0fb707faff573af97bad42390a9a3473002bdd1bbcceece5"
        }
    },
    "cpu": {
        "python_version": "3.11.1.final.0 (64 bit)",
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
}
```
</details>


### Execution Monitoring

#### CLI

Running `capsula monitor <commands>` in the project root (the directory where `capsula.toml` is located) monitors the execution of the specified commands. The context is logged in the `context.json` file in the capsule directory, and the command execution is logged in the `pre-run-info.json` and `post-run-info.json` files in the capsule directory.

For example, if you run `capsula monitor -i calculate-pi-cli python examples/calculate_pi_cli.py` in the root directory, you will get the following `pre-run-info.json` and `post-run-info.json` as output:

`pre-run-info.json`:

```json
{
    "root_directory": "/root/directory",
    "cwd": "/current/working/directory",
    "timestamp": "2023-07-12T18:09:29.490877+09:00",
    "args": [
        "python",
        "examples/calculate_pi_cli.py"
    ]
}
```

`post-run-info.json`:

```json
{
    "root_directory": "/root/directory",
    "timestamp": "2023-07-12T18:09:31.977784+09:00",
    "run_time": "PT2.486653S",
    "files": {
        "examples/pi_cli.png": {
            "hash_algorithm": "sha256",
            "file_hash": "00fd7975b3dba2fabfb201ef2c16dc992f3a6e98bff28232826be8a297b05b87"
        }
    },
    "stdout": "3.140888\n",
    "stderr": "",
    "exit_code": 0
}
```

#### Python decorator

The `capsula.monitor` decorator can be used to monitor the execution of a Python function. The context is logged in the `context.json` file in the capsule directory, and the function execution is logged in the `pre-run-info.json` and `post-run-info.json` files in the capsule directory.

Example usage:

```python
from pathlib import Path

import capsula

@capsula.monitor(
    directory=Path(__file__).parents[1], # Root directory
    include_return_value=True,
    items=("calculate-pi-dec",), # The name of the item to be monitored
)
def main(n: int, seed: int | None = None) -> float:
    """Calculate pi using the Monte Carlo method."""

    # Calculate pi and plot the result as a figure here

    output_path = Path(__file__).parent / "pi_dec.png"
    fig.savefig(str(output_path), dpi=300)

    return pi
```

If you call the above function with `main(1000000)`, the following files will be created in the capsule directory:

`pre-run-info.json`:

```json
{
    "root_directory": "/root/directory",
    "cwd": "/current/working/directory",
    "timestamp": "2023-07-12T22:21:01.787135+09:00",
    "source_file": "/path/to/calculate_pi_dec.py",
    "source_line": 12,
    "function_name": "main",
    "args": [
        1000000
    ],
    "kwargs": {}
}
```

`post-run-info.json`:

```json
{
    "root_directory": "/root/directory",
    "timestamp": "2023-07-12T22:21:04.011644+09:00",
    "run_time": "PT2.223863S",
    "files": {
        "examples/pi_dec.png": {
            "hash_algorithm": "sha256",
            "file_hash": "1786f6efee5e340545e23c5071a34493c43e8b2e37bb70d1b50f87bfd3ac0376"
        }
    },
    "return_value": 3.143432,
    "exception_info": null
}
```

## Try it out

### Prerequisites

- [Poetry](https://python-poetry.org/docs/#installation)

### Steps

1. Clone this repository:

```bash
git clone git@github.com:shunichironomura/capsula.git
```

2. Install the package, including the examples:

```bash
poetry install --with examples
```

3. Run the example:

Context capture:

```bash
capsula capture
```

Execution monitoring:

```bash
capsula monitor python examples/calculate_pi.py
```

## Roadmap

See [#1](https://github.com/shunichironomura/capsula/issues/1).
