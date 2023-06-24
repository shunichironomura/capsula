import platform as pf

from cpuinfo import get_cpu_info
from pydantic import BaseModel


class Architecture(BaseModel):
    bits: str = pf.architecture()[0]
    linkage: str = pf.architecture()[1]


class PythonInfo(BaseModel):
    executable_architecture: Architecture = Architecture()
    build_no: str = pf.python_build()[0]
    build_date: str = pf.python_build()[1]
    compiler: str = pf.python_compiler()
    branch: str = pf.python_branch()
    implementation: str = pf.python_implementation()
    version: str = pf.python_version()


class Platform(BaseModel):
    """Information about the platform."""

    machine: str = pf.machine()
    node: str = pf.node()
    platform: str = pf.platform()
    release: str = pf.release()
    version: str = pf.version()
    system: str = pf.system()
    processor: str = pf.processor()
    python: PythonInfo = PythonInfo()


class Environment(BaseModel):
    """Execution environment to be stored and used later."""

    platform: Platform = Platform()

    # There are many duplicates between the platform and cpu info.
    # We could remove the duplicates, but it's not worth the effort.
    cpu: dict = get_cpu_info()
