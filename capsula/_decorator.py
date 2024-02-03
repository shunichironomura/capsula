from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path
from random import choices
from string import ascii_letters, digits
from typing import TYPE_CHECKING, Callable, Literal, TypeVar

from capsula.utils import search_for_project_root

from ._backport import Concatenate, ParamSpec
from ._run import CapsuleParams, FuncInfo, Run

if TYPE_CHECKING:
    from ._capsule import Capsule
    from ._context import ContextBase
    from ._reporter import ReporterBase
    from ._watcher import WatcherBase

_P = ParamSpec("_P")
_T = TypeVar("_T")


def watcher(
    watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_watcher(watcher)
        return run

    return decorator


def reporter(
    reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
    mode: Literal["pre", "in", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_reporter(reporter, mode=mode)
        return run

    return decorator


def context(
    context: ContextBase | Callable[[CapsuleParams], ContextBase],
    mode: Literal["pre", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_context(context, mode=mode)
        return run

    return decorator


def run(
    run_dir: Path | Callable[[FuncInfo], Path] | None = None,
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def _default_run_dir_generator(func_info: FuncInfo) -> Path:
        project_root = search_for_project_root(Path(inspect.getfile(func_info.func)))
        random_suffix = "".join(choices(ascii_letters + digits, k=4))  # noqa: S311
        datetime_str = datetime.now(UTC).astimezone().strftime(r"%Y%m%d_%H%M%S")
        dir_name = f"{func_info.func.__name__}_{datetime_str}_{random_suffix}"
        return project_root / "vault" / dir_name

    run_dir = _default_run_dir_generator if run_dir is None else run_dir

    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.set_run_dir(run_dir)

        return run

    return decorator


def pass_pre_run_capsule(func: Callable[Concatenate[Capsule, _P], _T]) -> Run[_P, _T]:
    return Run(func, pass_pre_run_capsule=True)
