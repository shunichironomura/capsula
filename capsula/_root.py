from typing import Any

from .encapsulator import Encapsulator, _CapsuleItemKey


def record(key: _CapsuleItemKey, value: Any) -> None:
    enc = Encapsulator.get_current()
    if enc is None:
        msg = "No active encapsulator found."
        raise RuntimeError(msg)
    enc.record(key, value)
