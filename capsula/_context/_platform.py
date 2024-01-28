import platform as pf

from ._base import ContextBase


class PlatformContext(ContextBase):
    def encapsulate(self) -> dict:
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
