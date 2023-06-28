# Capsula

> :warning: **NOTE**: This project is still work in progress.

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of *Capsula* is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of a past command execution, fostering reproducibility and consistency over time.

## Features

1. **Context Capture (under development):** *Capsula* logs the details of the execution context for future reference and reproduction. The context includes, but not limited to, Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring (to be implemented):** *Capsula* monitors the execution of Python scripts, Jupyter notebooks, and CLI commands, logging information such as the execution status, output, duration, etc.

4. **Context Reproduction (to be implemented):** *Capsula* enables the reproduction of the captured context. This ensures the consistency and reproducibility of results.

## Installation

You can install *Capsula* via pip:

```bash
pip install capsula
```

At the root of your project, create a `capsula.toml` file wit the following content:

```toml
[capture]
vault-directory = 'vault'

subdirectory-template = '%Y%m%d_%H%M%S'

include-cpu = false

pre-capture-commands = [
    'poetry lock --check'
]

environment-variables = [
    'HOME',
]

[capture.files]
"pyproject.toml" = { hash = "sha256", copy = true }
"poetry.lock" = { hash = "sha256", copy = true }


[capture.git.repositories]
capsula = '.'
```


## Usage

### Context Capture

Running `capsula capture` in the project root (the directory where `capsula.toml` is located) captures the execution context and stores it in a vault directory. The vault directory is specified in the `capsula.toml` file. The vault directory is organized by subdirectories, each of which contains the captured context of a single execution. The subdirectory name is generated using the `subdirectory-template` option in the `capsula.toml` file. The default template is `%Y%m%d_%H%M%S`, which generates a subdirectory name in the format of `YYYYMMDD_HHMMSS`. The context is stored in a JSON file named `context.json`.

Example of `context.json`:

```json
{
    "platform": {
        "machine": "x86_64",
        "node": "DESKTOP-XXXXXXX",
        "platform": "Linux-5.15.90.1-microsoft-standard-WSL2-x86_64-with-glibc2.31",
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
    "cpu": null,
    "environment_variables": {
        "HOME": "/home/directory"
    },
    "cwd": "/current/working/directory",
    "git": {
        "capsula": {
            "path": ".",
            "sha": "7dbaa0389ca4553b3d8b6e35c2d0e4d9e2501764",
            "branch": "git-config",
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
            "file_hash": "e412f8efcdfc12aa7ec36f219a2037c90ade279df5fb11fdefa5a5c3f583a1df"
        },
        "poetry.lock": {
            "hash_algorithm": "sha256",
            "file_hash": "bd2ee84e4ab22528f89431ca4693c6db58aa304380b36cee7d3e21e19f756df2"
        }
    }
}
```

## Roadmap

See [#1](https://github.com/shunichironomura/capsula/issues/1).
