import sys
from pathlib import Path

from pydantic import BaseModel

from capsula.environment import Environment


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class FreezeConfig(BaseModel):
    """Configuration for the freeze command."""

    # Whether to include the Capsula version in the output file.
    # include_capsula_version: bool = True # noqa: ERA001

    class Config:  # noqa: D106
        alias_generator = to_hyphen_case
        populate_by_name = False
        extra = "forbid"


def freeze(
    *,
    config: FreezeConfig,
    output: Path | None = None,
) -> None:
    """Freeze the environment into a file."""
    env = Environment()

    # Write the environment to the output file.
    env_json = env.model_dump_json(
        indent=4,
    )
    if output is None:
        sys.stdout.write(env_json)
    else:
        with output.open("w") as output_file:
            output_file.write(env_json)
