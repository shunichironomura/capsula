from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping, TypedDict

from ._backport import tomllib
from ._context import ContextBase
from ._reporter import ReporterBase
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from ._run import CapsuleParams


def _construct_context(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], ContextBase] | ContextBase:
    context_class_name = raw_config.pop("type")
    context_class = ContextBase.get_subclass(context_class_name)
    return context_class.default(**raw_config)


def _construct_watcher(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], WatcherBase] | WatcherBase:
    watcher_class_name = raw_config.pop("type")
    watcher_class = WatcherBase.get_subclass(watcher_class_name)
    return watcher_class.default(**raw_config)


def _construct_reporter(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], ReporterBase] | ReporterBase:
    reporter_class_name = raw_config.pop("type")
    reporter_class = ReporterBase.get_subclass(reporter_class_name)
    return reporter_class.default(**raw_config)


class _PreRunConfig(TypedDict):
    context: list[Mapping[str, Callable[[CapsuleParams], ContextBase] | ContextBase]]
    reporter: list[Mapping[str, Callable[[CapsuleParams], ReporterBase] | ReporterBase]]


class _InRunConfig(TypedDict):
    watcher: list[Mapping[str, Callable[[CapsuleParams], WatcherBase] | WatcherBase]]
    reporter: list[Mapping[str, Callable[[CapsuleParams], ReporterBase] | ReporterBase]]


class _PostRunConfig(TypedDict):
    context: list[Mapping[str, Callable[[CapsuleParams], ContextBase] | ContextBase]]
    reporter: list[Mapping[str, Callable[[CapsuleParams], ReporterBase] | ReporterBase]]


_CapsulaConfig = TypedDict(
    "_CapsulaConfig",
    {
        "pre-run": _PreRunConfig,
        "in-run": _InRunConfig,
        "post-run": _PostRunConfig,
    },
)


def load_config(path: Path) -> _CapsulaConfig:
    with path.open("rb") as file:
        raw_config = tomllib.load(file)

    config: _CapsulaConfig = {
        "pre-run": {"context": [], "reporter": []},
        "in-run": {"watcher": [], "reporter": []},
        "post-run": {"context": [], "reporter": []},
    }

    if (pre_run := raw_config.get("pre-run")) is not None:
        config["pre-run"]["context"] = list(map(_construct_context, pre_run.get("context", [])))  # type: ignore[arg-type]
        config["pre-run"]["reporter"] = list(map(_construct_reporter, pre_run.get("reporter", [])))  # type: ignore[arg-type]
    if (in_run := raw_config.get("in-run")) is not None:
        config["in-run"]["watcher"] = list(map(_construct_watcher, in_run.get("watcher", [])))  # type: ignore[arg-type]
        config["in-run"]["reporter"] = list(map(_construct_reporter, in_run.get("reporter", [])))  # type: ignore[arg-type]
    if (post_run := raw_config.get("post-run")) is not None:
        config["post-run"]["context"] = list(map(_construct_context, post_run.get("context", [])))  # type: ignore[arg-type]
        config["post-run"]["reporter"] = list(map(_construct_reporter, post_run.get("reporter", [])))  # type: ignore[arg-type]

    return config


if __name__ == "__main__":
    print(load_config(Path(__file__).parent.parent / "capsula.toml"))