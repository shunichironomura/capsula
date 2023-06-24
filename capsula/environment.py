from __future__ import annotations

import platform as pf
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Self

from cpuinfo import get_cpu_info
from git.repo import Repo
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Hashable

    from capsula.capture import CaptureConfig


class EnvironmentItem(BaseModel, ABC):
    """Base class for environment items."""

    @classmethod
    @abstractmethod
    def capture(cls, config: CaptureConfig) -> Self | dict[Hashable, Self]:
        """Capture the environment item."""
        raise NotImplementedError


class Architecture(EnvironmentItem):
    bits: str
    linkage: str

    @classmethod
    def capture(cls, _: CaptureConfig) -> Self:
        return cls(
            bits=pf.architecture()[0],
            linkage=pf.architecture()[1],
        )


class PythonInfo(EnvironmentItem):
    executable_architecture: Architecture
    build_no: str
    build_date: str
    compiler: str
    branch: str
    implementation: str
    version: str

    @classmethod
    def capture(cls, config: CaptureConfig) -> Self:
        return cls(
            executable_architecture=Architecture.capture(config),
            build_no=pf.python_build()[0],
            build_date=pf.python_build()[1],
            compiler=pf.python_compiler(),
            branch=pf.python_branch(),
            implementation=pf.python_implementation(),
            version=pf.python_version(),
        )


class Platform(EnvironmentItem):
    """Information about the platform."""

    machine: str
    node: str
    platform: str
    release: str
    version: str
    system: str
    processor: str
    python: PythonInfo

    @classmethod
    def capture(cls, config: CaptureConfig) -> Self:
        return cls(
            machine=pf.machine(),
            node=pf.node(),
            platform=pf.platform(),
            release=pf.release(),
            version=pf.version(),
            system=pf.system(),
            processor=pf.processor(),
            python=PythonInfo.capture(config),
        )


class GitInfo(EnvironmentItem):
    sha: str

    @classmethod
    def capture(cls, config: CaptureConfig) -> dict[Path, Self]:
        git_infos = {}
        for repository in config.git_repositories:
            repo = Repo(repository)
            sha = repo.head.object.hexsha
            git_infos[repository] = cls(sha=sha)
        return git_infos


class Environment(EnvironmentItem):
    """Execution environment to be stored and used later."""

    platform: Platform

    # There are many duplicates between the platform and cpu info.
    # We could remove the duplicates, but it's not worth the effort.
    # We use the default factory to avoid the overhead of getting the CPU info, which is slow.
    cpu: dict | None = Field(default_factory=get_cpu_info)

    git: dict[Path, GitInfo] = Field(default_factory=dict)

    cwd: Path = Field(default_factory=Path.cwd)

    @classmethod
    def capture(cls, config: CaptureConfig) -> Self:
        return cls(
            platform=Platform.capture(config),
            cpu=get_cpu_info() if config.include_cpu else None,
            git=GitInfo.capture(config),
            cwd=Path.cwd(),
        )
