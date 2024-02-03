from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from git.repo import Repo

from capsula.exceptions import CapsulaError

from ._base import ContextBase

if TYPE_CHECKING:
    from capsula._decorator import CapsuleParams

logger = logging.getLogger(__name__)


class GitRepositoryDirtyError(CapsulaError):
    def __init__(self, repo: Repo) -> None:
        self.repo = repo
        super().__init__(f"Repository {repo.working_dir} is dirty")


class GitRepositoryContext(ContextBase):
    def __init__(
        self,
        name: str,
        *,
        path: Path | str,
        diff_file: Path | str | None = None,
        search_parent_directories: bool = False,
        allow_dirty: bool = False,
    ) -> None:
        self.name = name
        self.path = Path(path)
        self.search_parent_directories = search_parent_directories
        self.allow_dirty = allow_dirty
        self.diff_file = None if diff_file is None else Path(diff_file)

    def encapsulate(self) -> dict:
        repo = Repo(self.path, search_parent_directories=self.search_parent_directories)
        if not self.allow_dirty and repo.is_dirty():
            raise GitRepositoryDirtyError(repo)

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

    @classmethod
    def default(
        cls,
        name: str | None = None,
        *,
        allow_dirty: bool | None = None,
    ) -> Callable[[CapsuleParams], GitRepositoryContext]:
        def callback(params: CapsuleParams) -> GitRepositoryContext:
            func_file_path = Path(inspect.getfile(params.func))
            repo = Repo(func_file_path.parent, search_parent_directories=True)
            repo_name = Path(repo.working_dir).name
            return cls(
                name=Path(repo.working_dir).name if name is None else name,
                path=Path(repo.working_dir),
                diff_file=params.run_dir / f"{repo_name}.diff",
                search_parent_directories=False,
                allow_dirty=True if allow_dirty is None else allow_dirty,
            )

        return callback
