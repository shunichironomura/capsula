from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypedDict

from git.repo import Repo

from capsula._run import CommandInfo, FuncInfo
from capsula.exceptions import CapsulaError

from ._base import ContextBase

if TYPE_CHECKING:
    from os import PathLike

    from capsula._run import CapsuleParams

logger = logging.getLogger(__name__)


class GitRepositoryDirtyError(CapsulaError):
    def __init__(self, repo: Repo) -> None:
        self.repo = repo
        super().__init__(f"Repository {repo.working_dir} is dirty")


class _GitRepositoryContextData(TypedDict):
    working_dir: PathLike[str] | str
    sha: str
    remotes: dict[str, str]
    branch: str | None
    is_dirty: bool


class GitRepositoryContext(ContextBase):
    def __init__(
        self,
        name: str,
        *,
        path: Path | str,
        diff_file: Path | str | None = None,
        search_parent_directories: bool = False,
        allow_dirty: bool = True,
    ) -> None:
        self.name = name
        self.path = Path(path)
        self.search_parent_directories = search_parent_directories
        self.allow_dirty = allow_dirty
        self.diff_file = None if diff_file is None else Path(diff_file)

    def encapsulate(self) -> _GitRepositoryContextData:
        repo = Repo(self.path, search_parent_directories=self.search_parent_directories)
        if not self.allow_dirty and repo.is_dirty():
            raise GitRepositoryDirtyError(repo)

        def get_optional_branch_name(repo: Repo) -> str | None:
            try:
                return repo.active_branch.name
            except TypeError:
                return None

        info: _GitRepositoryContextData = {
            "working_dir": repo.working_dir,
            "sha": repo.head.commit.hexsha,
            "remotes": {remote.name: remote.url for remote in repo.remotes},
            "branch": get_optional_branch_name(repo),
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
        path: Path | str | None = None,
        allow_dirty: bool | None = None,
    ) -> Callable[[CapsuleParams], GitRepositoryContext]:
        def callback(params: CapsuleParams) -> GitRepositoryContext:
            if path is not None:
                repo = Repo(path, search_parent_directories=False)
            else:
                if isinstance(params.exec_info, FuncInfo):
                    repo_search_start_path = Path(inspect.getfile(params.exec_info.func)).parent
                elif isinstance(params.exec_info, CommandInfo) or params.exec_info is None:
                    repo_search_start_path = Path.cwd()
                else:
                    msg = f"exec_info must be an instance of FuncInfo or CommandInfo, not {type(params.exec_info)}."
                    raise TypeError(msg)
                repo = Repo(repo_search_start_path, search_parent_directories=True)

            repo_name = Path(repo.working_dir).name

            return cls(
                name=Path(repo.working_dir).name if name is None else name,
                path=Path(repo.working_dir),
                diff_file=params.run_dir / f"{repo_name}.diff",
                search_parent_directories=False,
                allow_dirty=True if allow_dirty is None else allow_dirty,
            )

        return callback
