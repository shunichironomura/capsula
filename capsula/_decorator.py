from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Tuple, TypeVar, Union

from capsula._reporter import ReporterBase
from capsula.encapsulator import Encapsulator

from ._backport import ParamSpec
from ._context import ContextBase
from ._run import CapsuleParams, FuncInfo, Run
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._backport import TypeAlias

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