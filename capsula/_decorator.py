from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Tuple, TypeVar, Union

from pydantic import BaseModel

from capsula._reporter import ReporterBase
from capsula.encapsulator import Encapsulator

from ._backport import ParamSpec
from ._context import ContextBase
from ._run import Run
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._backport import TypeAlias

_P = ParamSpec("_P")
_T = TypeVar("_T")


_ContextInput: TypeAlias = Union[
    ContextBase,
    Tuple[ContextBase, Tuple[str, ...]],
    Callable[[Path, Callable], Union[ContextBase, Tuple[ContextBase, Tuple[str, ...]]]],
]
_WatcherInput: TypeAlias = Union[
    WatcherBase,
    Tuple[WatcherBase, Tuple[str, ...]],
    Callable[[Path, Callable], Union[WatcherBase, Tuple[WatcherBase, Tuple[str, ...]]]],
]
_ReporterInput: TypeAlias = Union[ReporterBase, Callable[[Path, Callable], ReporterBase]]


def capsule(  # noqa: C901
    capsule_directory: Path | str | None = None,
    pre_run_contexts: Sequence[_ContextInput] | None = None,
    pre_run_reporters: Sequence[_ReporterInput] | None = None,
    in_run_watchers: Sequence[_WatcherInput] | None = None,
    post_run_contexts: Sequence[_ContextInput] | None = None,
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    if capsule_directory is None:
        raise NotImplementedError
    capsule_directory = Path(capsule_directory)

    assert pre_run_contexts is not None
    assert pre_run_reporters is not None
    assert in_run_watchers is not None
    assert post_run_contexts is not None

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        pre_run_enc = Encapsulator()
        for cxt in pre_run_contexts:
            if isinstance(cxt, ContextBase):
                pre_run_enc.add_context(cxt)
            elif isinstance(cxt, tuple):
                pre_run_enc.add_context(cxt[0], key=cxt[1])
            else:
                cxt_hydrated = cxt(capsule_directory, func)
                if isinstance(cxt_hydrated, ContextBase):
                    pre_run_enc.add_context(cxt_hydrated)
                elif isinstance(cxt_hydrated, tuple):
                    pre_run_enc.add_context(cxt_hydrated[0], key=cxt_hydrated[1])

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            capsule_directory.mkdir(parents=True, exist_ok=True)
            pre_run_capsule = pre_run_enc.encapsulate()
            for reporter in pre_run_reporters:
                if isinstance(reporter, ReporterBase):
                    reporter.report(pre_run_capsule)
                else:
                    reporter(capsule_directory, func).report(pre_run_capsule)

            return func(*args, **kwargs)

        return wrapper

    return decorator


class CapsuleParams(BaseModel):
    run_dir: Path
    func: Callable
    args: tuple
    kwargs: dict
    phase: Literal["pre", "in", "post"]


def watcher(
    watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase],
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def reporter(
    reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
    mode: Literal["pre", "in", "post", "all"],
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def context(
    context: ContextBase | Callable[[CapsuleParams], ContextBase],
    mode: Literal["pre", "in", "post", "all"],
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            return func(*args, **kwargs)

        return wrapper

    return decorator
