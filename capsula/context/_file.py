from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable, Literal, overload

from git.repo import Repo

from capsula.exceptions import CapsulaError
from capsula.hash import file_digest

from ._base import Context

logger = logging.getLogger(__name__)


class FileContext(Context):
    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: str | Callable[[], hashlib._Hash] | None,
        copy_to: Path | str | None = None,
        move_to: Path | str | None = None,
    ) -> None:
        self.path = Path(path)
        self.hash_algorithm = hash_algorithm
        self.copy_to = None if copy_to is None else Path(copy_to)
        self.move_to = None if move_to is None else Path(move_to)

    def encapsulate(self) -> dict:
        if self.hash_algorithm is None:
            digest = None
        else:
            with self.path.open("rb") as f:
                digest = file_digest(f, self.hash_algorithm).hexdigest()

        info = {
            "hash": {
                "algorithm": self.hash_algorithm,
                "digest": digest,
            },
        }
        return info

    def default_key(self) -> tuple[str, str]:
        return ("file", str(self.path))
