from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal, TypeVar

from ._backport import ParamSpec
from ._run import CapsuleParams, FuncInfo, Run

if TYPE_CHECKING:
    from pathlib import Path

    from capsula._reporter import ReporterBase

    from ._context import ContextBase
    from ._watcher import WatcherBase

_P = ParamSpec("_P")
_T = TypeVar("_T")


def watcher(
    watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        func = func_or_run.func if isinstance(func_or_run, Run) else func_or_run
        run = func_or_run if isinstance(func_or_run, Run) else Run(func)
        run.add_watcher(watcher)
        return run

    return decorator


def reporter(
    reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
    mode: Literal["pre", "in", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        func = func_or_run.func if isinstance(func_or_run, Run) else func_or_run
        run = func_or_run if isinstance(func_or_run, Run) else Run(func)
        run.add_reporter(reporter, mode=mode)
        return run

    return decorator


def context(
    context: ContextBase | Callable[[CapsuleParams], ContextBase],
    mode: Literal["pre", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        func = func_or_run.func if isinstance(func_or_run, Run) else func_or_run
        run = func_or_run if isinstance(func_or_run, Run) else Run(func)
        run.add_context(context, mode=mode)
        return run

    return decorator


def run(
    run_dir: Path | Callable[[FuncInfo], Path],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        func = func_or_run.func if isinstance(func_or_run, Run) else func_or_run
        run = func_or_run if isinstance(func_or_run, Run) else Run(func)
        run.set_run_dir(run_dir)

        return run

    return decorator
