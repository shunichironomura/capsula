from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, MutableMapping

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


def load_config(path: Path):
    with path.open("rb") as file:
        raw_config = tomllib.load(file)

    config = {
        "pre-run": {"context": [], "reporter": []},
        "in-run": {"watcher": [], "reporter": []},
        "post-run": {"context": [], "reporter": []},
    }

    if (pre_run := raw_config.get("pre-run")) is not None:
        config["pre-run"]["context"] = list(map(_construct_context, pre_run.get("context", [])))

    print(config)


if __name__ == "__main__":
    load_config(Path(__file__).parent.parent / "capsula.toml")
