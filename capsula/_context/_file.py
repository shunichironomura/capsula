from __future__ import annotations

import logging
from pathlib import Path
from shutil import copyfile, move
from typing import Iterable

from capsula._backport import file_digest

from ._base import ContextBase

logger = logging.getLogger(__name__)


class FileContext(ContextBase):
    def __init__(
        self,
        path: Path | str,
        *,
        hash_algorithm: str | None,
        copy_to: Iterable[Path | str] | Path | str | None = None,
        move_to: Path | str | None = None,
    ) -> None:
        self.path = Path(path)
        self.hash_algorithm = hash_algorithm
        self.move_to = None if move_to is None else Path(move_to)

        if copy_to is None:
            self.copy_to: tuple[Path, ...] = ()
        elif isinstance(copy_to, (str, Path)):
            self.copy_to = (Path(copy_to),)
        else:
            self.copy_to = tuple(Path(p) for p in copy_to)

    def _normalize_copy_dst_path(self, p: Path) -> Path:
        if p.is_dir():
            return p / self.path.name
        else:
            return p

    def encapsulate(self) -> dict:
        if self.hash_algorithm is None:
            digest = None
        else:
            with self.path.open("rb") as f:
                digest = file_digest(f, self.hash_algorithm).hexdigest()

        self.copy_to = tuple(self._normalize_copy_dst_path(p) for p in self.copy_to)

        info: dict = {
            "hash": {
                "algorithm": self.hash_algorithm,
                "digest": digest,
            },
            "copied_to": self.copy_to,
            "moved_to": self.move_to,
        }

        for path in self.copy_to:
            copyfile(self.path, path)
        if self.move_to is not None:
            move(self.path, self.move_to)

        return info

    def default_key(self) -> tuple[str, str]:
        return ("file", str(self.path))
