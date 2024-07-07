from __future__ import annotations

from typing import Any

from cpuinfo import get_cpu_info

from ._base import ContextBase


class CpuContext(ContextBase):
    """Context to capture CPU information."""

    def encapsulate(self) -> dict[str, Any]:
        return get_cpu_info()  # type: ignore[no-any-return]

    def default_key(self) -> str:
        return "cpu"
