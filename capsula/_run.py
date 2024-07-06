from __future__ import annotations

import inspect
import logging
import queue
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import choices
from string import ascii_letters, digits
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, TypeVar, Union, overload

from ._backport import Concatenate, ParamSpec, Self, TypeAlias
from ._context import ContextBase, FunctionCallContext
from ._encapsulator import Encapsulator
from ._reporter import ReporterBase
from ._utils import search_for_project_root
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from types import TracebackType

    from ._capsule import Capsule

_P = ParamSpec("_P")
_T = TypeVar("_T")

logger = logging.getLogger(__name__)


@dataclass
class FuncInfo:
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass
class CommandInfo:
    command: str


@dataclass
class CapsuleParams:
    exec_info: FuncInfo | CommandInfo | None
    run_dir: Path
    phase: Literal["pre", "in", "post"]
    project_root: Path


ExecInfo: TypeAlias = Union[FuncInfo, CommandInfo]


def generate_default_run_dir(exec_info: ExecInfo | None = None) -> Path:
    exec_name: str | None
    project_root = get_project_root(exec_info)
    if exec_info is None:
        exec_name = None
    elif isinstance(exec_info, CommandInfo):
        exec_name = exec_info.command.split()[0]  # TODO: handle more complex commands
    elif isinstance(exec_info, FuncInfo):
        exec_name = exec_info.func.__name__
    else:
        msg = f"exec_info must be an instance of FuncInfo or CommandInfo, not {type(exec_info)}."
        raise TypeError(msg)

    random_suffix = "".join(choices(ascii_letters + digits, k=4))  # noqa: S311
    datetime_str = datetime.now(timezone.utc).astimezone().strftime(r"%Y%m%d_%H%M%S")
    dir_name = ("" if exec_name is None else f"{exec_name}_") + f"{datetime_str}_{random_suffix}"
    return project_root / "vault" / dir_name


def get_project_root(exec_info: ExecInfo | None = None) -> Path:
    if exec_info is None or isinstance(exec_info, CommandInfo):
        return search_for_project_root(Path.cwd())
    elif isinstance(exec_info, FuncInfo):
        return search_for_project_root(Path(inspect.getfile(exec_info.func)))
    else:
        msg = f"exec_info must be an instance of FuncInfo or CommandInfo, not {type(exec_info)}."
        raise TypeError(msg)


class Run(Generic[_P, _T]):
    _thread_local = threading.local()

    @classmethod
    def _get_run_stack(cls) -> queue.LifoQueue[Self]:
        if not hasattr(cls._thread_local, "run_stack"):
            cls._thread_local.run_stack = queue.LifoQueue()
        return cls._thread_local.run_stack  # type: ignore[no-any-return]

    @classmethod
    def get_current(cls) -> Self | None:
        try:
            return cls._get_run_stack().queue[-1]
        except IndexError:
            return None

    @overload
    def __init__(self, func: Callable[_P, _T], *, pass_pre_run_capsule: Literal[False] = False) -> None: ...

    @overload
    def __init__(
        self,
        func: Callable[Concatenate[Capsule, _P], _T],
        *,
        pass_pre_run_capsule: Literal[True],
    ) -> None: ...

    def __init__(
        self,
        func: Callable[_P, _T] | Callable[Concatenate[Capsule, _P], _T],
        *,
        pass_pre_run_capsule: bool = False,
    ) -> None:
        self._pre_run_context_generators: deque[Callable[[CapsuleParams], ContextBase]] = deque()
        self._in_run_watcher_generators: deque[Callable[[CapsuleParams], WatcherBase]] = deque()
        self._post_run_context_generators: deque[Callable[[CapsuleParams], ContextBase]] = deque()

        self._pre_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = deque()
        self._in_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = deque()
        self._post_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = deque()

        self._pass_pre_run_capsule: bool = pass_pre_run_capsule
        self._func: Callable[_P, _T] | Callable[Concatenate[Capsule, _P], _T] = func

        self._run_dir_generator: Callable[[FuncInfo], Path] | None = None
        self._run_dir: Path | None = None

    @property
    def run_dir(self) -> Path:
        if self._run_dir is None:
            msg = "run_dir must be set before accessing it."
            raise ValueError(msg)
        return self._run_dir

    def add_context(
        self,
        context: ContextBase | Callable[[CapsuleParams], ContextBase],
        *,
        mode: Literal["pre", "post", "all"],
        append_left: bool = False,
    ) -> None:
        def context_generator(params: CapsuleParams) -> ContextBase:
            if isinstance(context, ContextBase):
                return context
            else:
                return context(params)

        if mode == "pre":
            if append_left:
                self._pre_run_context_generators.appendleft(context_generator)
            else:
                self._pre_run_context_generators.append(context_generator)
        elif mode == "post":
            if append_left:
                self._post_run_context_generators.appendleft(context_generator)
            else:
                self._post_run_context_generators.append(context_generator)
        elif mode == "all":
            if append_left:
                self._pre_run_context_generators.appendleft(context_generator)
                self._post_run_context_generators.appendleft(context_generator)
            else:
                self._pre_run_context_generators.append(context_generator)
                self._post_run_context_generators.append(context_generator)
        else:
            msg = f"mode must be one of 'pre', 'post', or 'all', not {mode}."
            raise ValueError(msg)

    def add_watcher(
        self,
        watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase],
        *,
        append_left: bool = False,
    ) -> None:
        def watcher_generator(params: CapsuleParams) -> WatcherBase:
            if isinstance(watcher, WatcherBase):
                return watcher
            else:
                return watcher(params)

        if append_left:
            self._in_run_watcher_generators.appendleft(watcher_generator)
        else:
            self._in_run_watcher_generators.append(watcher_generator)

    def add_reporter(  # noqa: C901, PLR0912
        self,
        reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
        *,
        mode: Literal["pre", "in", "post", "all"],
        append_left: bool = False,
    ) -> None:
        def reporter_generator(params: CapsuleParams) -> ReporterBase:
            if isinstance(reporter, ReporterBase):
                return reporter
            else:
                return reporter(params)

        if mode == "pre":
            if append_left:
                self._pre_run_reporter_generators.appendleft(reporter_generator)
            else:
                self._pre_run_reporter_generators.append(reporter_generator)
        elif mode == "in":
            if append_left:
                self._in_run_reporter_generators.appendleft(reporter_generator)
            else:
                self._in_run_reporter_generators.append(reporter_generator)
        elif mode == "post":
            if append_left:
                self._post_run_reporter_generators.appendleft(reporter_generator)
            else:
                self._post_run_reporter_generators.append(reporter_generator)
        elif mode == "all":
            if append_left:
                self._pre_run_reporter_generators.appendleft(reporter_generator)
                self._in_run_reporter_generators.appendleft(reporter_generator)
                self._post_run_reporter_generators.appendleft(reporter_generator)
            else:
                self._pre_run_reporter_generators.append(reporter_generator)
                self._in_run_reporter_generators.append(reporter_generator)
                self._post_run_reporter_generators.append(reporter_generator)
        else:
            msg = f"mode must be one of 'pre', 'in', 'post', or 'all', not {mode}."
            raise ValueError(msg)

    def set_run_dir(self, run_dir: Path | Callable[[FuncInfo], Path]) -> None:
        def run_dir_generator(params: FuncInfo) -> Path:
            if isinstance(run_dir, Path):
                return run_dir
            else:
                return run_dir(params)

        self._run_dir_generator = run_dir_generator

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

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T:  # noqa: C901
        func_info = FuncInfo(func=self._func, args=args, kwargs=kwargs)
        if self._run_dir_generator is None:
            msg = "run_dir_generator must be set before calling the function."
            raise ValueError(msg)
        self._run_dir = self._run_dir_generator(func_info)
        self._run_dir.mkdir(parents=True, exist_ok=True)
        params = CapsuleParams(
            exec_info=func_info,
            run_dir=self._run_dir,
            phase="pre",
            project_root=get_project_root(func_info),
        )

        pre_run_enc = Encapsulator()
        for context_generator in self._pre_run_context_generators:
            context = context_generator(params)
            pre_run_enc.add_context(context)
        pre_run_capsule = pre_run_enc.encapsulate()
        for reporter_generator in self._pre_run_reporter_generators:
            reporter = reporter_generator(params)
            reporter.report(pre_run_capsule)

        params.phase = "in"
        in_run_enc = Encapsulator()
        for watcher_generator in self._in_run_watcher_generators:
            watcher = watcher_generator(params)
            in_run_enc.add_watcher(watcher)

        in_run_enc.add_context(FunctionCallContext(self._func, args, kwargs))

        try:
            with self, in_run_enc, in_run_enc.watch():
                if self._pass_pre_run_capsule:
                    result = self._func(pre_run_capsule, *args, **kwargs)  # type: ignore[arg-type]
                else:
                    result = self._func(*args, **kwargs)
        finally:
            in_run_capsule = in_run_enc.encapsulate()
            for reporter_generator in self._in_run_reporter_generators:
                reporter = reporter_generator(params)
                try:
                    reporter.report(in_run_capsule)
                except Exception:
                    logger.exception(f"Failed to report in-run capsule with reporter {reporter}.")

            params.phase = "post"
            post_run_enc = Encapsulator()
            for context_generator in self._post_run_context_generators:
                context = context_generator(params)
                post_run_enc.add_context(context)
            post_run_capsule = post_run_enc.encapsulate()
            for reporter_generator in self._post_run_reporter_generators:
                reporter = reporter_generator(params)
                try:
                    reporter.report(post_run_capsule)
                except Exception:
                    logger.exception(f"Failed to report post-run capsule with reporter {reporter}.")

        return result
