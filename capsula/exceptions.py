__all__ = ["CapsulaError", "CapsulaConfigurationError"]


class CapsulaError(Exception):
    pass


class CapsulaConfigurationError(CapsulaError):
    pass
