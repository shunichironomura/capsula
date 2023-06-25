from __future__ import annotations

import os
import platform as pf
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Literal, Self

from cpuinfo import get_cpu_info
from git.repo import Repo
from pydantic import BaseModel, Field

from capsula.hash import compute_hash

if TYPE_CHECKING:
    from collections.abc import Hashable

    from capsula.capture import CaptureConfig


class ContextItem(BaseModel, ABC):
    """Base class for context items."""

    @classmethod
    @abstractmethod
    def capture(cls, config: CaptureConfig) -> Self | dict[Hashable, Self]:
        """Capture the context item."""
        raise NotImplementedError


class Architecture(ContextItem):
    bits: str
    linkage: str

    @classmethod
    def capture(cls, _: CaptureConfig) -> Self:
        return cls(
            bits=pf.architecture()[0],
            linkage=pf.architecture()[1],
        )


class PythonInfo(ContextItem):
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


class Platform(ContextItem):
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


class GitRemote(BaseModel):
    name: str
    url: str


class GitInfo(ContextItem):
    path: Path
    sha: str
    branch: str
    remotes: list[GitRemote]

    @classmethod
    def capture(cls, config: CaptureConfig) -> dict[Path, Self]:
        git_infos = {}
        for name, path in config.git_repositories.items():
            repo = Repo(path)
            git_infos[name] = cls(
                path=path,
                sha=repo.head.object.hexsha,
                remotes=[GitRemote(name=remote.name, url=remote.url) for remote in repo.remotes],
                branch=repo.active_branch.name,
            )

            diff = repo.git.diff()
            with (config.subdirectory / f"{name}.diff").open("w") as diff_file:
                diff_file.write(diff)

        return git_infos


class FileContext(ContextItem):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"]
    file_hash: str = Field(..., alias="hash")

    @classmethod
    def capture(cls, config: CaptureConfig) -> dict[Path, Self]:
        files = {}
        for path, file_config in config.files.items():
            files[path] = cls(
                hash=compute_hash(path, file_config.hash_algorithm),
                hash_algorithm=file_config.hash_algorithm,
            )
            if file_config.copy_:
                copyfile(path, config.subdirectory / path.name)

        return files


class Context(ContextItem):
    """Execution context to be stored and used later."""

    platform: Platform

    # There are many duplicates between the platform and cpu info.
    # We could remove the duplicates, but it's not worth the effort.
    # We use the default factory to avoid the overhead of getting the CPU info, which is slow.
    cpu: dict | None

    environment_variables: dict[str, str]

    cwd: Path

    git: dict[Path, GitInfo]

    files: dict[Path, FileContext]

    @classmethod
    def capture(cls, config: CaptureConfig) -> Self:
        return cls(
            platform=Platform.capture(config),
            cpu=get_cpu_info() if config.include_cpu else None,
            environment_variables={name: os.environ[name] for name in config.environment_variables},
            git=GitInfo.capture(config),
            cwd=Path.cwd(),
            files=FileContext.capture(config),
        )
