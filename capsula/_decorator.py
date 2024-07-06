from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, TypeVar

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
    watcher: WatcherBase | Callable[[CapsuleParams], WatcherBase],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        # No need to set append_left=True here, as watchers are added as the outermost context manager
        run.add_watcher(watcher, append_left=False)
        return run

    return decorator


def reporter(
    reporter: ReporterBase | Callable[[CapsuleParams], ReporterBase],
    mode: Literal["pre", "in", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_reporter(reporter, mode=mode, append_left=True)
        return run

    return decorator


def context(
    context: ContextBase | Callable[[CapsuleParams], ContextBase],
    mode: Literal["pre", "post", "all"],
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
    def decorator(func_or_run: Callable[_P, _T] | Run[_P, _T]) -> Run[_P, _T]:
        run = func_or_run if isinstance(func_or_run, Run) else Run(func_or_run)
        run.add_context(context, mode=mode, append_left=True)
        return run

    return decorator


def run(
    run_dir: Path | Callable[[FuncInfo], Path] | None = None,
    *,
    ignore_config: bool = False,
    config_path: Path | str | None = None,
) -> Callable[[Callable[_P, _T] | Run[_P, _T]], Run[_P, _T]]:
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


def pass_pre_run_capsule(func: Callable[Concatenate[Capsule, _P], _T]) -> Run[_P, _T]:
    return Run(func, pass_pre_run_capsule=True)
