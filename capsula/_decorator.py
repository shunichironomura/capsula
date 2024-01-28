from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Tuple, TypeVar, Union

from capsula.encapsulator import Encapsulator
from capsula.reporter import Reporter

from ._backport import ParamSpec
from ._context import Context
from .watcher import Watcher

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._backport import TypeAlias

_P = ParamSpec("_P")
_T = TypeVar("_T")


_ContextInput: TypeAlias = Union[
    Context,
    Tuple[Context, Tuple[str, ...]],
    Callable[[Path, Callable], Union[Context, Tuple[Context, Tuple[str, ...]]]],
]
_WatcherInput: TypeAlias = Union[
    Watcher,
    Tuple[Watcher, Tuple[str, ...]],
    Callable[[Path, Callable], Union[Watcher, Tuple[Watcher, Tuple[str, ...]]]],
]
_ReporterInput: TypeAlias = Union[Reporter, Callable[[Path, Callable], Reporter]]


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
            if isinstance(cxt, Context):
                pre_run_enc.add_context(cxt)
            elif isinstance(cxt, tuple):
                pre_run_enc.add_context(cxt[0], key=cxt[1])
            else:
                cxt_hydrated = cxt(capsule_directory, func)
                if isinstance(cxt_hydrated, Context):
                    pre_run_enc.add_context(cxt_hydrated)
                elif isinstance(cxt_hydrated, tuple):
                    pre_run_enc.add_context(cxt_hydrated[0], key=cxt_hydrated[1])

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            capsule_directory.mkdir(parents=True, exist_ok=True)
            pre_run_capsule = pre_run_enc.encapsulate()
            for reporter in pre_run_reporters:
                if isinstance(reporter, Reporter):
                    reporter.report(pre_run_capsule)
                else:
                    reporter(capsule_directory, func).report(pre_run_capsule)

            return func(*args, **kwargs)

        return wrapper

    return decorator
