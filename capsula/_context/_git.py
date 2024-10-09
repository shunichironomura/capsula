from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Callable, TypedDict

from git.repo import Repo
from typing_extensions import Doc

from capsula._exceptions import CapsulaError
from capsula._run import CommandInfo, FuncInfo

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
    diff_file: PathLike[str] | str | None


class GitRepositoryContext(ContextBase):
    """Context to capture a Git repository."""

    @classmethod
    def builder(
        cls,
        name: Annotated[
            str | None,
            Doc("Name of the Git repository. If not provided, the name of the working directory will be used."),
        ] = None,
        *,
        path: Annotated[
            Path | str | None,
            Doc(
                "Path to the Git repository. If not provided, the parent directories of the file where the function is "
                "defined will be searched for a Git repository.",
            ),
        ] = None,
        path_relative_to_project_root: Annotated[
            bool,
            Doc(
                "Whether `path` is relative to the project root. Will be ignored if `path` is None or absolute. "
                "If True, it will be interpreted as relative to the project root. "
                "If False, `path` will be interpreted as relative to the current working directory. "
                "It is recommended to set this to True in the configuration file.",
            ),
        ] = False,
        allow_dirty: Annotated[bool, Doc("Whether to allow the repository to be dirty")] = True,
    ) -> Callable[[CapsuleParams], GitRepositoryContext]:
        def build(params: CapsuleParams) -> GitRepositoryContext:
            if path_relative_to_project_root and path is not None and not Path(path).is_absolute():
                repository_path: Path | None = params.project_root / path
            else:
                repository_path = Path(path) if path is not None else None

            if repository_path is not None:
                repo = Repo(repository_path, search_parent_directories=False)
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
                allow_dirty=allow_dirty,
            )

        return build

    def __init__(
        self,
        name: str,
        *,
        path: Path | str,
        diff_file: Path | str | None = None,
        search_parent_directories: bool = False,
        allow_dirty: bool = True,
    ) -> None:
        self._name = name
        self._path = Path(path)
        self._search_parent_directories = search_parent_directories
        self._allow_dirty = allow_dirty
        self._diff_file = None if diff_file is None else Path(diff_file)

    def encapsulate(self) -> _GitRepositoryContextData:
        repo = Repo(self._path, search_parent_directories=self._search_parent_directories)
        if not self._allow_dirty and repo.is_dirty():
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
            "diff_file": None,
        }

        diff_txt = repo.git.diff()
        if diff_txt:
            assert self._diff_file is not None, "diff_file is None"
            with self._diff_file.open("w") as f:
                f.write(diff_txt)
            logger.debug(f"Wrote diff to {self._diff_file}")
            info["diff_file"] = self._diff_file
        return info

    def default_key(self) -> tuple[str, str]:
        return ("git", self._name)
