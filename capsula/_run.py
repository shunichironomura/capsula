from __future__ import annotations

import queue
import threading
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Callable, Generic, Literal, Self, Tuple, TypeVar, Union

from click import Context
from pydantic import BaseModel

from capsula._reporter import ReporterBase
from capsula.encapsulator import Encapsulator

from ._backport import ParamSpec
from ._context import ContextBase
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._backport import TypeAlias

_P = ParamSpec("_P")
_T = TypeVar("_T")


class FuncInfo(BaseModel):
    func: Callable
    args: tuple
    kwargs: dict


class CapsuleParams(FuncInfo):
    run_dir: Path
    phase: Literal["pre", "in", "post"]


class Run(Generic[_P, _T]):
    _thread_local = threading.local()

    @classmethod
    def _get_run_stack(cls) -> queue.LifoQueue[Self]:
        if not hasattr(cls._thread_local, "run_stack"):
            cls._thread_local.run_stack = queue.LifoQueue()
        return cls._thread_local.run_stack

    @classmethod
    def get_current(cls) -> Self | None:
        try:
            return cls._get_run_stack().queue[-1]
        except IndexError:
            return None

    def __init__(self, func: Callable[_P, _T]) -> None:
        self.pre_run_context_generators: list[Callable[[CapsuleParams], ContextBase]] = []
        self.in_run_watcher_generators: list[Callable[[CapsuleParams], WatcherBase]] = []
        self.post_run_context_generators: list[Callable[[CapsuleParams], ContextBase]] = []

        self.pre_run_reporter_generators: list[Callable[[CapsuleParams], ReporterBase]] = []
        self.in_run_reporter_generators: list[Callable[[CapsuleParams], ReporterBase]] = []
        self.post_run_reporter_generators: list[Callable[[CapsuleParams], ReporterBase]] = []

        self.func = func
        self.run_dir_generator: Callable[[FuncInfo], Path] | None = None

    def add_context(
        self,
        context: ContextBase | Callable[[CapsuleParams], ContextBase],
        *,
        mode: Literal["pre", "post", "all"],
    ) -> None:
        def context_generator(params: CapsuleParams) -> ContextBase:
            if isinstance(context, ContextBase):
                return context
            else:
                return context(params)

        if mode == "pre":
            self.pre_run_context_generators.append(context_generator)
        elif mode == "post":
            self.post_run_context_generators.append(context_generator)
        elif mode == "all":
            self.pre_run_context_generators.append(context_generator)
            self.post_run_context_generators.append(context_generator)
        else:
            msg = f"mode must be one of 'pre', 'post', or 'all', not {mode}."
            raise ValueError(msg)

    def add_watcher(self, watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase]) -> None:
        def watcher_generator(params: CapsuleParams) -> WatcherBase:
            if isinstance(watcher, WatcherBase):
                return watcher
            else:
                return watcher(params)

        self.in_run_watcher_generators.append(watcher_generator)

    def add_reporter(
        self,
        reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
        *,
        mode: Literal["pre", "in", "post", "all"],
    ) -> None:
        def reporter_generator(params: CapsuleParams) -> ReporterBase:
            if isinstance(reporter, ReporterBase):
                return reporter
            else:
                return reporter(params)

        if mode == "pre":
            self.pre_run_reporter_generators.append(reporter_generator)
        elif mode == "in":
            self.in_run_reporter_generators.append(reporter_generator)
        elif mode == "post":
            self.post_run_reporter_generators.append(reporter_generator)
        elif mode == "all":
            self.pre_run_reporter_generators.append(reporter_generator)
            self.in_run_reporter_generators.append(reporter_generator)
            self.post_run_reporter_generators.append(reporter_generator)
        else:
            msg = f"mode must be one of 'pre', 'in', 'post', or 'all', not {mode}."
            raise ValueError(msg)

    def set_run_dir(self, run_dir: Path | Callable[[FuncInfo], Path]) -> None:
        def run_dir_generator(params: FuncInfo) -> Path:
            if isinstance(run_dir, Path):
                return run_dir
            else:
                return run_dir(params)

        self.run_dir_generator = run_dir_generator

    def __enter__(self) -> Self:
        self._get_run_stack().put(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._get_run_stack().get(block=False)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        func_info = FuncInfo(func=self.func, args=args, kwargs=kwargs)
        if self.run_dir_generator is None:
            msg = "run_dir_generator must be set before calling the function."
            raise ValueError(msg)
        run_dir = self.run_dir_generator(func_info)
        run_dir.mkdir(parents=True, exist_ok=True)
        params = CapsuleParams(
            func=func_info.func,
            args=func_info.args,
            kwargs=func_info.kwargs,
            run_dir=run_dir,
            phase="pre",
        )

        pre_run_enc = Encapsulator()
        for context_generator in self.pre_run_context_generators:
            context = context_generator(params)
            pre_run_enc.add_context(context)
        pre_run_capsule = pre_run_enc.encapsulate()
        for reporter_generator in self.pre_run_reporter_generators:
            reporter = reporter_generator(params)
            reporter.report(pre_run_capsule)

        params.phase = "in"
        in_run_enc = Encapsulator()
        for watcher_generator in self.in_run_watcher_generators:
            watcher = watcher_generator(params)
            in_run_enc.add_watcher(watcher)

        with self, in_run_enc, in_run_enc.watch():
            result = self.func(*args, **kwargs)

        in_run_capsule = in_run_enc.encapsulate()
        for reporter_generator in self.in_run_reporter_generators:
            reporter = reporter_generator(params)
            reporter.report(in_run_capsule)

        params.phase = "post"
        post_run_enc = Encapsulator()
        for context_generator in self.post_run_context_generators:
            context = context_generator(params)
            post_run_enc.add_context(context)
        post_run_capsule = post_run_enc.encapsulate()
        for reporter_generator in self.post_run_reporter_generators:
            reporter = reporter_generator(params)
            reporter.report(post_run_capsule)

        return result
