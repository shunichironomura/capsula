from __future__ import annotations

import logging
import warnings
from pathlib import Path
from shutil import copyfile, move
from typing import TYPE_CHECKING, Annotated, Callable, TypedDict

from typing_extensions import Doc

from capsula._backport import file_digest

from ._base import ContextBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from capsula._run import CapsuleParams

logger = logging.getLogger(__name__)


class _FileContextData(TypedDict):
    copied_to: tuple[Path, ...]
    moved_to: Path | None
    hash: dict[str, str] | None


class FileContext(ContextBase):
    """Context to capture a file."""

    _default_hash_algorithm = "sha256"

    @classmethod
    def builder(
        cls,
        path: Annotated[Path | str, Doc("Path to the file")],
        *,
        compute_hash: Annotated[bool, Doc("Whether to compute the hash of the file")] = True,
        hash_algorithm: Annotated[
            str | None,
            Doc(
                "Hash algorithm to use. This will be fed to `hashlib.file_digest` as the `digest` argument. "
                "If not provided, `sha256` will be used.",
            ),
        ] = None,
        copy: Annotated[bool, Doc("Whether to copy the file to the run directory")] = False,
        move: Annotated[bool, Doc("Whether to move the file to the run directory")] = False,
        ignore_missing: Annotated[bool, Doc("Whether to ignore if the file does not exist")] = False,
        path_relative_to_project_root: Annotated[
            bool,
            Doc(
                "Whether `path` is relative to the project root. Will be ignored if `path` is absolute. "
                "If True, it will be interpreted as relative to the project root. "
                "If False, `path` will be interpreted as relative to the current working directory. "
                "It is recommended to set this to True in the configuration file.",
            ),
        ] = False,
    ) -> Callable[[CapsuleParams], FileContext]:
        if copy and move:
            warnings.warn("Both copy and move are True. Only move will be performed.", UserWarning, stacklevel=2)
            move = True
            copy = False

        def build(params: CapsuleParams) -> FileContext:
            if path_relative_to_project_root and path is not None and not Path(path).is_absolute():
                file_path = params.project_root / path
            else:
                file_path = Path(path)

            return cls(
                path=file_path,
                compute_hash=compute_hash,
                hash_algorithm=hash_algorithm,
                copy_to=params.run_dir if copy else None,
                move_to=params.run_dir if move else None,
                ignore_missing=ignore_missing,
            )

        return build

    def __init__(
        self,
        path: Path | str,
        *,
        compute_hash: bool = True,
        hash_algorithm: str | None = None,
        copy_to: Iterable[Path | str] | Path | str | None = None,
        move_to: Path | str | None = None,
        ignore_missing: bool = False,
    ) -> None:
        self._path = Path(path)
        self._hash_algorithm = self._default_hash_algorithm if hash_algorithm is None else hash_algorithm
        self._compute_hash = compute_hash
        self._move_to = None if move_to is None else Path(move_to)
        self._ignore_missing = ignore_missing

        if copy_to is None:
            self._copy_to: tuple[Path, ...] = ()
        elif isinstance(copy_to, (str, Path)):
            self._copy_to = (Path(copy_to),)
        else:
            self._copy_to = tuple(Path(p) for p in copy_to)

    def _normalize_copy_dst_path(self, p: Path) -> Path:
        if p.is_dir():
            return p / self._path.name
        else:
            return p

    def encapsulate(self) -> _FileContextData:
        if not self._path.exists():
            if self._ignore_missing:
                logger.warning(f"File {self._path} does not exist. Ignoring.")
                return _FileContextData(copied_to=(), moved_to=None, hash=None)
            else:
                msg = f"File {self._path} does not exist."
                raise FileNotFoundError(msg)
        self._copy_to = tuple(self._normalize_copy_dst_path(p) for p in self._copy_to)

        if self._compute_hash:
            with self._path.open("rb") as f:
                digest = file_digest(f, self._hash_algorithm).hexdigest()
            hash_data = {
                "algorithm": self._hash_algorithm,
                "digest": digest,
            }
        else:
            hash_data = None

        info: _FileContextData = {
            "copied_to": self._copy_to,
            "moved_to": self._move_to,
            "hash": hash_data,
        }

        for path in self._copy_to:
            copyfile(self._path, path)
        if self._move_to is not None:
            move(str(self._path), self._move_to)

        return info

    def default_key(self) -> tuple[str, str]:
        return ("file", str(self._path))
