from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Callable, Literal, TypeVar

from typing_extensions import Doc

from ._backport import Concatenate, ParamSpec
from ._config import load_config
from ._run import (
    CapsuleParams,
    ExecInfo,
    FuncInfo,
    Run,
    RunDtoNoPassPreRunCapsule,
    RunDtoPassPreRunCapsule,
    default_run_name_factory,
)
from ._utils import get_default_config_path, search_for_project_root

if TYPE_CHECKING:
    from datetime import datetime

    from ._capsule import Capsule
    from ._context import ContextBase
    from ._reporter import ReporterBase
    from ._watcher import WatcherBase

P = ParamSpec("P")
T = TypeVar("T")


def watcher(
    watcher: Annotated[
        WatcherBase | Callable[[CapsuleParams], WatcherBase],
        Doc("Watcher or a builder function to create a watcher from the capsule parameters."),
    ],
) -> Annotated[
    Callable[
        [Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]],
        RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ],
    Doc("Decorator to add a watcher to the in-run phase of the run."),
]:
    """Decorator to add a watcher to the in-run phase of the run.

    Example:
    ```python
    import capsula

    @capsula.run()
    @capsula.watcher(capsula.UncaughtExceptionWatcher())
    def func() -> None: ...
    ```

    """

    def decorator(
        func_or_run: Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ) -> RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]:
        run_dto = (
            func_or_run
            if isinstance(func_or_run, (RunDtoNoPassPreRunCapsule, RunDtoPassPreRunCapsule))
            else RunDtoNoPassPreRunCapsule(func=func_or_run)
        )
        # No need to set append_left=True here, as watchers are added as the outermost context manager
        run_dto.add_watcher(watcher, append_left=False)
        return run_dto

    return decorator


def reporter(
    reporter: Annotated[
        ReporterBase | Callable[[CapsuleParams], ReporterBase],
        Doc("Reporter or a builder function to create a reporter from the capsule parameters."),
    ],
    mode: Annotated[
        Literal["pre", "in", "post", "all"],
        Doc("Phase to add the reporter. Specify 'all' to add to all phases."),
    ],
) -> Annotated[
    Callable[
        [Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]],
        RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ],
    Doc("Decorator to add a reporter to the specified phase of the run."),
]:
    """Decorator to add a reporter to the specified phase of the run.

    Example:
    ```python
    import capsula

    @capsula.run()
    @capsula.reporter(capsula.JsonDumpReporter.builder(), mode="all")
    def func() -> None: ...
    ```

    """

    def decorator(
        func_or_run: Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ) -> RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]:
        run = (
            func_or_run
            if isinstance(func_or_run, (RunDtoPassPreRunCapsule, RunDtoNoPassPreRunCapsule))
            else RunDtoNoPassPreRunCapsule(func=func_or_run)
        )
        run.add_reporter(reporter, mode=mode, append_left=True)
        return run

    return decorator


def context(
    context: Annotated[
        ContextBase | Callable[[CapsuleParams], ContextBase],
        Doc("Context or a builder function to create a context from the capsule parameters."),
    ],
    mode: Annotated[
        Literal["pre", "post", "all"],
        Doc("Phase to add the context. Specify 'all' to add to all phases."),
    ],
) -> Annotated[
    Callable[
        [Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]],
        RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ],
    Doc("Decorator to add a context to the specified phase of the run."),
]:
    """Decorator to add a context to the specified phase of the run.

    Example:
    ```python
    import capsula

    @capsula.run()
    @capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
    def func() -> None: ...
    ```

    """

    def decorator(
        func_or_run: Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ) -> RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]:
        run = (
            func_or_run
            if isinstance(func_or_run, (RunDtoNoPassPreRunCapsule, RunDtoPassPreRunCapsule))
            else RunDtoNoPassPreRunCapsule(func=func_or_run)
        )
        run.add_context(context, mode=mode, append_left=True)
        return run

    return decorator


_NOT_SET = object()


def run(  # noqa: C901
    *,
    run_name_factory: Annotated[
        Callable[[FuncInfo, str, datetime], str] | None,
        Doc("Function to generate the run name. If not specified, the default run name factory will be used."),
    ] = None,
    ignore_config: Annotated[bool, Doc("Whether to ignore the configuration file.")] = False,
    config_path: Annotated[
        Path | str | None,
        Doc("Path to the configuration file. If not specified, the default configuration file will be used."),
    ] = None,
    vault_dir: Annotated[
        Path | str | None,
        Doc("Path to the vault directory."),
    ] = None,
) -> Annotated[
    Callable[[Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T]], Run[P, T]],
    Doc("Decorator to create a `Run` object."),
]:
    """Decorator to create a `Run` object.

    Place this decorator at the outermost position of the decorators.

    Example:
    ```python
    import capsula

    @capsula.run() # This should come first
    @capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
    ...  # Add more decorators
    def func() -> None: ...
    ```

    The vault directory is determined by the following priority:
    1. If `vault_dir` argument is set, it will be used as the vault directory.
    2. If `ignore_config` argument is False and `vault-dir` field is present in the config file,
       it will be used as the vault directory.
    3. The default vault directory is used.

    The run name factory is determined by the following priority:
    1. If `run_name_factory` argument is set, it will be used as the run name.
    2. The default run name factory is used.

    """
    if run_name_factory is not None:
        # Adjust the function signature of the run name factory
        def _run_name_factory_adjusted(info: ExecInfo | None, random_str: str, timestamp: datetime, /) -> str:
            if isinstance(info, FuncInfo):
                return run_name_factory(info, random_str, timestamp)
            raise TypeError("The run name factory must accept the `FuncInfo` object as the first argument.")
    else:
        _run_name_factory_adjusted = default_run_name_factory

    def decorator(
        func_or_run: Callable[P, T] | RunDtoNoPassPreRunCapsule[P, T] | RunDtoPassPreRunCapsule[P, T],
    ) -> Run[P, T]:
        run_dto = (
            func_or_run
            if isinstance(func_or_run, (RunDtoNoPassPreRunCapsule, RunDtoPassPreRunCapsule))
            else RunDtoNoPassPreRunCapsule(func=func_or_run)
        )
        run_dto.run_name_factory = _run_name_factory_adjusted
        run_dto.vault_dir = Path(vault_dir) if vault_dir is not None else None

        if not ignore_config:
            config = load_config(get_default_config_path() if config_path is None else Path(config_path))
            for phase in ("pre", "in", "post"):
                phase_key = f"{phase}-run"
                if phase_key not in config:
                    continue
                for context in reversed(config[phase_key].get("contexts", [])):  # type: ignore[literal-required]
                    assert phase in {"pre", "post"}, f"Invalid phase for context: {phase}"
                    run_dto.add_context(context, mode=phase, append_left=True)  # type: ignore[arg-type]
                for watcher in reversed(config[phase_key].get("watchers", [])):  # type: ignore[literal-required]
                    assert phase == "in", "Watcher can only be added to the in-run phase."
                    # No need to set append_left=True here, as watchers are added as the outermost context manager
                    run_dto.add_watcher(watcher, append_left=False)
                for reporter in reversed(config[phase_key].get("reporters", [])):  # type: ignore[literal-required]
                    assert phase in {"pre", "in", "post"}, f"Invalid phase for reporter: {phase}"
                    run_dto.add_reporter(reporter, mode=phase, append_left=True)

            run_dto.vault_dir = config["vault-dir"] if run_dto.vault_dir is None else run_dto.vault_dir

        # Set the vault directory if it is not set by the config file
        if run_dto.vault_dir is None:
            assert run_dto.func is not None
            project_root = search_for_project_root(Path(inspect.getfile(run_dto.func)))
            run_dto.vault_dir = project_root / "vault"

        return Run(run_dto)

    return decorator


def pass_pre_run_capsule(
    func: Annotated[Callable[Concatenate[Capsule, P], T], Doc("Function to decorate.")],
) -> Annotated[RunDtoPassPreRunCapsule[P, T], Doc("Decorated function as a `Run` object.")]:
    """Decorator to pass the pre-run capsule to the function.

    This decorator must be placed closer to the function than the other decorators such as
    `run`, `context`, `watcher`, and `reporter`.

    The decorated function's first argument must be a `Capsule` object to receive the pre-run capsule.

    With this decorator, you can access the pre-run capsule in the function to get the data recorded by the contexts,
    such as the Git repository context. Here is an example, assuming the `GitRepositoryContext` for the "my-repo"
    repository is added to the pre-run phase:

    ```python
    import capsula

    @capsula.run()
    @capsula.pass_pre_run_capsule
    def func(pre_run_capsule: capsula.Capsule) -> None:
        git_sha = pre_run_capsule.data[("git", "my-repo")]["sha"]
    ```
    """
    return RunDtoPassPreRunCapsule(func=func)
