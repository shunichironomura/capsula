import os
from pathlib import Path


def set_capsule_dir(path: Path | str) -> None:
    """Set the capsule directory used by the monitor CLI."""
    os.environ["CAPSULE_DIR"] = str(path)


def get_capsule_dir() -> Path:
    """Get the capsule directory used by the monitor CLI."""
    try:
        return Path(os.environ["CAPSULE_DIR"])
    except KeyError as e:
        msg = "CAPSULE_DIR is not set. Run `capsula monitor <args>` to set it."
        raise RuntimeError(msg) from e
