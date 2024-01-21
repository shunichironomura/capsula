from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable, Literal, overload

from git.repo import Repo

from capsula.exceptions import CapsulaError
from capsula.hash import HashAlgorithm, compute_hash

from ._base import Context

logger = logging.getLogger(__name__)


class FileContext(Context):
    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: Callable[..., hashlib._Hash] | None,
        copy_to: Path | str | None = None,
        move_to: Path | str | None = None,
    ) -> None:
        self.path = Path(path)
        self.hash_algorithm = hash_algorithm
        self.copy_to = None if copy_to is None else Path(copy_to)
        self.move_to = None if move_to is None else Path(move_to)

    def encapsulate(self) -> dict:
        info = {
            "hash": None if self.hash_algorithm is None else compute_hash(self.path, self.hash_algorithm),
        }

        diff_txt = repo.git.diff()
        if diff_txt:
            assert self.diff_file is not None, "diff_file is None"
            with self.diff_file.open("w") as f:
                f.write(diff_txt)
            logger.debug(f"Wrote diff to {self.diff_file}")
        return info

    def default_key(self) -> tuple[str, str]:
        return ("file", str(self.path))
