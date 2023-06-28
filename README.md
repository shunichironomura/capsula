# Capsula

> :warning: **NOTE**: This project is still work in progress.

*Capsula*, a Latin word meaning *box*, is a Python package designed to help researchers and developers easily capture and reproduce their command execution context. The primary aim of *Capsula* is to tackle the reproducibility problem by providing a way to capture the execution context at any point in time, preserving it for future use. This ensures that you can reproduce the exact conditions of a past command execution, fostering reproducibility and consistency over time.

## Features

1. **Context Capture:** *Capsula* logs the details of the execution context for future reference and reproduction. The context includes, but not limited to, Python version, system environment variables, and the Git commit hash of the current working directory.

2. **Execution Monitoring (to be implemented):** *Capsula* monitors the execution of Python scripts, Jupyter notebooks, and CLI commands, logging information such as the execution status, output, duration, etc.

4. **Context Reproduction (to be implemented):** *Capsula* enables the reproduction of the captured context. This ensures the consistency and reproducibility of results.

## Installation

You can install *Capsula* via pip:

```bash
pip install capsula
```
