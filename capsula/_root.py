from __future__ import annotations

from typing import Any

from ._run import Run
from .encapsulator import Encapsulator, _CapsuleItemKey


def record(key: _CapsuleItemKey, value: Any) -> None:
    enc = Encapsulator.get_current()
    if enc is None:
        msg = "No active encapsulator found."
        raise RuntimeError(msg)
    enc.record(key, value)


def current_run_name() -> str:
    run: Run | None = Run.get_current()
    if run is None:
        msg = "No active run found."
        raise RuntimeError(msg)
    if run.run_dir is None:
        msg = "No active run directory found."
        raise RuntimeError(msg)
    return run.run_dir.name
