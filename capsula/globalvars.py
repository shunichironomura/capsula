import os
from pathlib import Path


def set_capsule_dir(path: Path | str) -> None:
    """Set the capsule directory used by the CLI."""
    os.environ["CAPSULA_CAPSULE_DIR"] = str(path)


def get_capsule_dir() -> Path:
    """Get the capsule directory used by the CLI."""
    try:
        return Path(os.environ["CAPSULA_CAPSULE_DIR"])
    except KeyError as e:
        msg = "CAPSULA_CAPSULE_DIR is not set."
        raise ValueError(msg) from e


def set_capsule_name(name: str) -> None:
    """Set the capsule name used by the CLI."""
    os.environ["CAPSULA_CAPSULE_NAME"] = name


def get_capsule_name() -> str:
    """Get the capsule name used by the CLI."""
    try:
        return os.environ["CAPSULA_CAPSULE_NAME"]
    except KeyError as e:
        msg = "CAPSULA_CAPSULE_NAME is not set."
        raise ValueError(msg) from e
