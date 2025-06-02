from __future__ import annotations

__all__ = ["CapsulaConfigurationError", "CapsulaError", "CapsulaUninitializedError"]


class CapsulaError(Exception):
    pass


class CapsulaConfigurationError(CapsulaError):
    pass


class CapsulaUninitializedError(CapsulaError):
    def __init__(self, *uninitialized_names: str) -> None:
        super().__init__(f"Uninitialized objects: {', '.join(uninitialized_names)}")


class CapsulaNoRunError(CapsulaError):
    def __init__(self) -> None:
        super().__init__("No run is active")
