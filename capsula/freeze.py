from pydantic import BaseModel


def to_hyphen_case(string: str) -> str:
    return string.replace("_", "-")


class FreezeConfig(BaseModel):
    """Configuration for the freeze command."""

    # Path to the output file.

    # Whether to include the Capsula version in the output file.
    include_capsula_version: bool = True

    class Config:  # noqa: D106
        alias_generator = to_hyphen_case
        populate_by_name = False
        extra = "forbid"


def freeze(config: FreezeConfig) -> None:
    """Freeze the environment into a file."""
