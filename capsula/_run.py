from __future__ import annotations

import inspect
import logging
import queue
import subprocess
import threading
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from random import choices
from string import ascii_letters, digits
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, TypeVar, Union

from capsula._exceptions import CapsulaUninitializedError

from ._backport import Concatenate, ParamSpec, Self, TypeAlias
from ._context import ContextBase
from ._encapsulator import Encapsulator
from ._exceptions import CapsulaError, CapsulaNoRunError
from ._reporter import ReporterBase
from ._utils import search_for_project_root
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from types import TracebackType

    from ._capsule import Capsule

P = ParamSpec("P")
T = TypeVar("T")
_P = ParamSpec("_P")
_T = TypeVar("_T")

logger = logging.getLogger(__name__)


@dataclass
class FuncInfo:
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    pass_pre_run_capsule: bool

    @property
    def bound_args(self) -> OrderedDict[str, Any]:
        signature = inspect.signature(self.func)
        ba = signature.bind(*self.args, **self.kwargs)
        ba.apply_defaults()
        return ba.arguments


@dataclass
class CommandInfo:
    command: tuple[str, ...]


@dataclass
class CapsuleParams:
    exec_info: FuncInfo | CommandInfo | None
    run_name: str
    run_dir: Path
    phase: Literal["pre", "in", "post"]
    project_root: Path


ExecInfo: TypeAlias = Union[FuncInfo, CommandInfo]


def get_default_vault_dir(exec_info: ExecInfo | None) -> Path:
    project_root = get_project_root(exec_info)
    return project_root / "vault"


def default_run_name_factory(exec_info: ExecInfo | None, random_str: str, timestamp: datetime, /) -> str:
    exec_name: str | None
    if exec_info is None:
        exec_name = None
    elif isinstance(exec_info, CommandInfo):
        exec_name = exec_info.command[0]
    elif isinstance(exec_info, FuncInfo):
        exec_name = exec_info.func.__name__
    else:
        msg = f"exec_info must be an instance of FuncInfo or CommandInfo, not {type(exec_info)}."
        raise TypeError(msg)

    datetime_str = timestamp.astimezone().strftime(r"%Y%m%d_%H%M%S")
    return ("" if exec_name is None else f"{exec_name}_") + f"{datetime_str}_{random_str}"


def get_project_root(exec_info: ExecInfo | None = None) -> Path:
    if exec_info is None or isinstance(exec_info, CommandInfo):
        return search_for_project_root(Path.cwd())
    elif isinstance(exec_info, FuncInfo):
        return search_for_project_root(Path(inspect.getfile(exec_info.func)))
    else:
        msg = f"exec_info must be an instance of FuncInfo or CommandInfo, not {type(exec_info)}."
        raise TypeError(msg)


@dataclass
class _RunDtoBase:
    run_name_factory: Callable[[ExecInfo | None, str, datetime], str] | None = None
    vault_dir: Path | None = None
    pre_run_context_generators: deque[Callable[[CapsuleParams], ContextBase]] = field(default_factory=deque)
    in_run_watcher_generators: deque[Callable[[CapsuleParams], WatcherBase]] = field(default_factory=deque)
    post_run_context_generators: deque[Callable[[CapsuleParams], ContextBase]] = field(default_factory=deque)
    pre_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = field(default_factory=deque)
    in_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = field(default_factory=deque)
    post_run_reporter_generators: deque[Callable[[CapsuleParams], ReporterBase]] = field(default_factory=deque)

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
                self.pre_run_context_generators.appendleft(context_generator)
            else:
                self.pre_run_context_generators.append(context_generator)
        elif mode == "post":
            if append_left:
                self.post_run_context_generators.appendleft(context_generator)
            else:
                self.post_run_context_generators.append(context_generator)
        elif mode == "all":
            if append_left:
                self.pre_run_context_generators.appendleft(context_generator)
                self.post_run_context_generators.appendleft(context_generator)
            else:
                self.pre_run_context_generators.append(context_generator)
                self.post_run_context_generators.append(context_generator)
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
            self.in_run_watcher_generators.appendleft(watcher_generator)
        else:
            self.in_run_watcher_generators.append(watcher_generator)

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
                self.pre_run_reporter_generators.appendleft(reporter_generator)
            else:
                self.pre_run_reporter_generators.append(reporter_generator)
        elif mode == "in":
            if append_left:
                self.in_run_reporter_generators.appendleft(reporter_generator)
            else:
                self.in_run_reporter_generators.append(reporter_generator)
        elif mode == "post":
            if append_left:
                self.post_run_reporter_generators.appendleft(reporter_generator)
            else:
                self.post_run_reporter_generators.append(reporter_generator)
        elif mode == "all":
            if append_left:
                self.pre_run_reporter_generators.appendleft(reporter_generator)
                self.in_run_reporter_generators.appendleft(reporter_generator)
                self.post_run_reporter_generators.appendleft(reporter_generator)
            else:
                self.pre_run_reporter_generators.append(reporter_generator)
                self.in_run_reporter_generators.append(reporter_generator)
                self.post_run_reporter_generators.append(reporter_generator)
        else:
            msg = f"mode must be one of 'pre', 'in', 'post', or 'all', not {mode}."
            raise ValueError(msg)


@dataclass
class RunDtoPassPreRunCapsule(_RunDtoBase, Generic[P, T]):
    func: Callable[Concatenate[Capsule, P], T] | None = None


@dataclass
class RunDtoNoPassPreRunCapsule(_RunDtoBase, Generic[P, T]):
    func: Callable[P, T] | None = None


@dataclass
class RunDtoCommand(_RunDtoBase):
    command: tuple[str, ...] | None = None


class Run(Generic[P, T]):
    _thread_local = threading.local()

    @classmethod
    def _get_run_stack(cls) -> queue.LifoQueue[Self]:
        if not hasattr(cls._thread_local, "run_stack"):
            cls._thread_local.run_stack = queue.LifoQueue()
        return cls._thread_local.run_stack  # type: ignore[no-any-return]

    @classmethod
    def get_current(cls) -> Self:
        try:
            return cls._get_run_stack().queue[-1]
        except IndexError as e:
            raise CapsulaNoRunError from e

    def __init__(
        self,
        run_dto: RunDtoPassPreRunCapsule[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoCommand,
        /,
    ) -> None:
        self._pre_run_context_generators = run_dto.pre_run_context_generators
        self._in_run_watcher_generators = run_dto.in_run_watcher_generators
        self._post_run_context_generators = run_dto.post_run_context_generators

        self._pre_run_reporter_generators = run_dto.pre_run_reporter_generators
        self._in_run_reporter_generators = run_dto.in_run_reporter_generators
        self._post_run_reporter_generators = run_dto.post_run_reporter_generators

        self._pass_pre_run_capsule: bool = isinstance(run_dto, RunDtoPassPreRunCapsule)

        if run_dto.run_name_factory is None:
            raise CapsulaUninitializedError("run_name_factory")
        self._run_name_factory: Callable[[ExecInfo | None, str, datetime], str] = run_dto.run_name_factory

        if run_dto.vault_dir is None:
            raise CapsulaUninitializedError("vault_dir")
        self._vault_dir: Path = run_dto.vault_dir

        self._run_dir: Path | None = None

        if isinstance(run_dto, RunDtoCommand):
            if run_dto.command is None:
                raise CapsulaUninitializedError("command")
            self._func: Callable[P, T] | Callable[Concatenate[Capsule, P], T] | None = None
            self._command: tuple[str, ...] | None = run_dto.command
        elif isinstance(run_dto, (RunDtoPassPreRunCapsule, RunDtoNoPassPreRunCapsule)):
            if run_dto.func is None:
                raise CapsulaUninitializedError("func")
            self._func = run_dto.func
            self._command = None
        else:
            msg = "run_dto must be an instance of RunDtoCommand, RunDtoPassPreRunCapsule, or RunDtoNoPassPreRunCapsule,"
            " not {type(run_dto)}."
            raise TypeError(msg)

    @property
    def run_dir(self) -> Path:
        if self._run_dir is None:
            msg = "run_dir must be set before accessing it."
            raise ValueError(msg)
        return self._run_dir

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

    def pre_run(self, exec_info: ExecInfo) -> tuple[CapsuleParams, Capsule]:
        if self._vault_dir.exists():
            if not self._vault_dir.is_dir():
                msg = f"Vault directory {self._vault_dir} exists but is not a directory."
                raise CapsulaError(msg)
        else:
            self._vault_dir.mkdir(parents=True, exist_ok=False)
            # If this is a new vault directory, create a .gitignore file in it
            # and write "*" to it
            gitignore_path = self._vault_dir / ".gitignore"
            with gitignore_path.open("w") as gitignore_file:
                gitignore_file.write("*\n")
        logger.info(f"Vault directory: {self._vault_dir}")

        # Generate the run name
        run_name = self._run_name_factory(
            exec_info,
            "".join(choices(ascii_letters + digits, k=4)),
            datetime.now(timezone.utc),
        )
        logger.info(f"Run name: {run_name}")

        self._run_dir = self._vault_dir / run_name
        try:
            self._run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.exception(
                f"Run directory {self._run_dir} already exists. Aborting to prevent overwriting existing data. "
                "Make sure that run_name_factory produces unique names.",
            )
            raise
        logger.info(f"Run directory: {self._run_dir}")

        params = CapsuleParams(
            exec_info=exec_info,
            run_name=run_name,
            run_dir=self._run_dir,
            phase="pre",
            project_root=get_project_root(exec_info),
        )

        pre_run_enc = Encapsulator()
        for context_generator in self._pre_run_context_generators:
            context = context_generator(params)
            pre_run_enc.add_context(context)
        pre_run_capsule = pre_run_enc.encapsulate()
        for reporter_generator in self._pre_run_reporter_generators:
            reporter = reporter_generator(params)
            reporter.report(pre_run_capsule)

        return params, pre_run_capsule

    def post_run(self, params: CapsuleParams) -> Capsule:
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

        return post_run_capsule

    def in_run(self, params: CapsuleParams, func: Callable[[], _T]) -> _T:
        params.phase = "in"
        in_run_enc = Encapsulator()
        for watcher_generator in self._in_run_watcher_generators:
            watcher = watcher_generator(params)
            in_run_enc.add_watcher(watcher)

        with self, in_run_enc, in_run_enc.watch():
            result = func()

        in_run_capsule = in_run_enc.encapsulate()
        for reporter_generator in self._in_run_reporter_generators:
            reporter = reporter_generator(params)
            try:
                reporter.report(in_run_capsule)
            except Exception:
                logger.exception(f"Failed to report in-run capsule with reporter {reporter}.")

        return result

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        assert self._func is not None
        func_info = FuncInfo(func=self._func, args=args, kwargs=kwargs, pass_pre_run_capsule=self._pass_pre_run_capsule)
        params, pre_run_capsule = self.pre_run(func_info)

        if self._pass_pre_run_capsule:

            def _func_1() -> T:
                assert self._func is not None
                return self._func(pre_run_capsule, *args, **kwargs)  # type: ignore[arg-type]

            func = _func_1
        else:

            def _func_2() -> T:
                assert self._func is not None
                return self._func(*args, **kwargs)  # type: ignore[arg-type]

            func = _func_2

        try:
            result = self.in_run(params, func)
        finally:
            _post_run_capsule = self.post_run(params)

        return result

    def exec_command(self) -> tuple[subprocess.CompletedProcess[str], CapsuleParams]:
        assert self._command is not None
        command_info = CommandInfo(command=self._command)
        params, _pre_run_capsule = self.pre_run(command_info)

        def func() -> subprocess.CompletedProcess[str]:
            assert self._command is not None
            return subprocess.run(self._command, check=False, capture_output=True, text=True)  # noqa: S603

        try:
            result = self.in_run(params, func)
        finally:
            _post_run_capsule = self.post_run(params)

        return result, params
