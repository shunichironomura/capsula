from __future__ import annotations

import platform as pf
from typing import TypedDict

from ._base import ContextBase


class _PlatformContextData(TypedDict):
    machine: str
    node: str
    platform: str
    release: str
    version: str
    system: str
    processor: str
    python: dict[str, str | dict[str, str]]


class PlatformContext(ContextBase):
    """Context to capture platform information, including Python version."""

    def encapsulate(self) -> _PlatformContextData:
        return {
            "machine": pf.machine(),
            "node": pf.node(),
            "platform": pf.platform(),
            "release": pf.release(),
            "version": pf.version(),
            "system": pf.system(),
            "processor": pf.processor(),
            "python": {
                "executable_architecture": {
                    "bits": pf.architecture()[0],
                    "linkage": pf.architecture()[1],
                },
                "build_no": pf.python_build()[0],
                "build_date": pf.python_build()[1],
                "compiler": pf.python_compiler(),
                "branch": pf.python_branch(),
                "implementation": pf.python_implementation(),
                "version": pf.python_version(),
            },
        }

    def default_key(self) -> str:
        return "platform"
