from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, TypeVar

from typing_extensions import Annotated, Doc

from ._backport import Concatenate, ParamSpec
from ._config import load_config
from ._run import CapsuleParams, FuncInfo, Run, generate_default_run_dir
from ._utils import get_default_config_path

if TYPE_CHECKING:
    from ._capsule import Capsule
    from ._context import ContextBase
    from ._reporter import ReporterBase
    from ._watcher import WatcherBase

_P = ParamSpec("_P")
_T = TypeVar("_T")


def watcher(
    watcher: Annotated[
        WatcherBase | Callable[[CapsuleParams], WatcherBase],
        Doc("Watcher or a builder function to create a watcher from the capsule parameters."),
    ],
) -> Annotated[
    Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]],
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

    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        # No need to set append_left=True here, as watchers are added as the outermost context manager
        run.add_watcher(watcher, append_left=False)
        return run

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
    Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]],
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

    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
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
    Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]],
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

    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_context(context, mode=mode, append_left=True)
        return run

    return decorator


def run(
    run_dir: Annotated[
        Path | Callable[[FuncInfo], Path] | None,
        Doc("Run directory to use. If not specified, a default run directory will be generated."),
    ] = None,
    *,
    ignore_config: Annotated[bool, Doc("Whether to ignore the configuration file.")] = False,
    config_path: Annotated[
        Path | str | None,
        Doc("Path to the configuration file. If not specified, the default configuration file will be used."),
    ] = None,
) -> Annotated[Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]], Doc("Decorator to create a `Run` object.")]:
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

    """
    run_dir = generate_default_run_dir if run_dir is None else run_dir

    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.set_run_dir(run_dir)

        if not ignore_config:
            config = load_config(get_default_config_path() if config_path is None else Path(config_path))
            for phase in ("pre", "in", "post"):
                phase_key = f"{phase}-run"
                if phase_key not in config:
                    continue
                for context in reversed(config[phase_key].get("contexts", [])):  # type: ignore[literal-required]
                    assert phase in {"pre", "post"}, f"Invalid phase for context: {phase}"
                    run.add_context(context, mode=phase, append_left=True)  # type: ignore[arg-type]
                for watcher in reversed(config[phase_key].get("watchers", [])):  # type: ignore[literal-required]
                    assert phase == "in", "Watcher can only be added to the in-run phase."
                    # No need to set append_left=True here, as watchers are added as the outermost context manager
                    run.add_watcher(watcher, append_left=False)
                for reporter in reversed(config[phase_key].get("reporters", [])):  # type: ignore[literal-required]
                    assert phase in {"pre", "in", "post"}, f"Invalid phase for reporter: {phase}"
                    run.add_reporter(reporter, mode=phase, append_left=True)  # type: ignore[arg-type]

        return run

    return decorator


def pass_pre_run_capsule(
    func: Annotated[Callable[Concatenate[Capsule, _P], _T], Doc("Function to decorate.")],
) -> Annotated[Run[_P, _T], Doc("Decorated function as a `Run` object.")]:
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
    return Run(func, pass_pre_run_capsule=True)
