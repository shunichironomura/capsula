#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
# ]
# ///

from pathlib import Path
from typing import NoReturn

import tomllib
import typer


def main(
    pyproject_path: Path,
) -> NoReturn:
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    version_str = pyproject["project"]["version"]
    print(version_str)

if __name__ == "__main__":
    typer.run(main)
