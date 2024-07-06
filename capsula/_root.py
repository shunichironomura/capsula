from __future__ import annotations

from typing import Any

from ._encapsulator import Encapsulator, _CapsuleItemKey
from ._run import Run


def record(key: _CapsuleItemKey, value: Any) -> None:
    enc = Encapsulator.get_current()
    if enc is None:
        msg = "No active encapsulator found."
        raise RuntimeError(msg)
    enc.record(key, value)


def current_run_name() -> str:
    run: Run[Any, Any] | None = Run.get_current()
    if run is None:
        msg = "No active run found."
        raise RuntimeError(msg)
    return run.run_dir.name
