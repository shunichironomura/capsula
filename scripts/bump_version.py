#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "rich",
#     "tomlkit",
#     "typer",
# ]
# ///

from enum import Enum
from pathlib import Path
from typing import NoReturn

import tomlkit
import typer
from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)


class BumpRule(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def main(
    pyproject_path: Path,
    bump_rule: BumpRule,
) -> NoReturn:
    stderr.print(f"Bumping version with rule: {bump_rule}")

    with pyproject_path.open("r") as f:
        pyproject = tomlkit.load(f)

    version_str: str = pyproject["project"]["version"]  # type: ignore[assignment, index]
    version_parts = version_str.split(".")
    if len(version_parts) != 3:
        msg = f"Version must have 3 parts, but {version_str!r} has {len(version_parts)}"
        raise ValueError(msg)
    major, minor, patch = map(int, version_parts)

    if bump_rule == BumpRule.MAJOR:
        major += 1
        minor = 0
        patch = 0
    elif bump_rule == BumpRule.MINOR:
        minor += 1
        patch = 0
    elif bump_rule == BumpRule.PATCH:
        patch += 1
    else:
        msg = f"Unknown bump rule: {bump_rule}"
        raise ValueError(msg)

    new_version_str = f"{major}.{minor}.{patch}"
    stderr.print(f"Bumping version from {version_str!r} to {new_version_str!r}")

    pyproject["project"]["version"] = new_version_str  # type: ignore[index]

    with pyproject_path.open("w") as f:
        tomlkit.dump(pyproject, f)
    stderr.print(f"Updated {pyproject_path}")

    stdout.print(new_version_str)
    raise typer.Exit(0)


if __name__ == "__main__":
    typer.run(main)
