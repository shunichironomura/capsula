#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "tomli; python_version < '3.11'",
#     "typer",
# ]
# ///

import sys
from pathlib import Path
from typing import NoReturn

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

import typer


def main(
    pyproject_path: Path,
) -> NoReturn:
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    version_str = pyproject["project"]["version"]
    print(version_str)
    raise typer.Exit(0)


if __name__ == "__main__":
    typer.run(main)
