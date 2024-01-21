from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable, Literal, overload

from git.repo import Repo

from capsula.exceptions import CapsulaError
from capsula.hash import HashAlgorithm

from ._base import Context

logger = logging.getLogger(__name__)


class FileContext(Context):
    # Overload to prevent users from setting both copy and move to True
    @overload
    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: Callable[..., hashlib._Hash],
        copy: Literal[False] = False,
        move: bool = False,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: Callable[..., hashlib._Hash],
        copy: bool = False,
        move: Literal[False] = False,
    ) -> None:
        ...

    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: Callable[..., hashlib._Hash],
        copy=False,
        move=False,
    ) -> None:
        self.path = Path(path)
        self.hash_algorithm = hash_algorithm

        if copy and move:
            msg = "copy and move cannot both be True"
            raise CapsulaError(msg)
        self.copy = copy
        self.move = move

    def encapsulate(self) -> dict:
        info = {
            "working_dir": repo.working_dir,
            "sha": repo.head.commit.hexsha,
            "remotes": {remote.name: remote.url for remote in repo.remotes},
            "branch": repo.active_branch.name,
            "is_dirty": repo.is_dirty(),
        }

        diff_txt = repo.git.diff()
        if diff_txt:
            assert self.diff_file is not None, "diff_file is None"
            with self.diff_file.open("w") as f:
                f.write(diff_txt)
            logger.debug(f"Wrote diff to {self.diff_file}")
        return info

    def default_key(self) -> tuple[str, str]:
        return ("git", self.name)
