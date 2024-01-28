from cpuinfo import get_cpu_info

from ._base import ContextBase


class CpuContext(ContextBase):
    def encapsulate(self) -> dict:
        return get_cpu_info()

    def default_key(self) -> str:
        return "cpu"
