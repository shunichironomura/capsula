from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, TypedDict

from ._backport import tomllib
from ._context import ContextBase
from ._reporter import ReporterBase
from ._watcher import WatcherBase

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from ._run import CapsuleParams


def _construct_context(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], ContextBase] | ContextBase:
    context_class_name = raw_config.pop("type")
    context_class = ContextBase.get_subclass(context_class_name)
    return context_class.builder(**raw_config)


def _construct_watcher(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], WatcherBase] | WatcherBase:
    watcher_class_name = raw_config.pop("type")
    watcher_class = WatcherBase.get_subclass(watcher_class_name)
    return watcher_class.builder(**raw_config)


def _construct_reporter(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], ReporterBase] | ReporterBase:
    reporter_class_name = raw_config.pop("type")
    reporter_class = ReporterBase.get_subclass(reporter_class_name)
    return reporter_class.builder(**raw_config)


class _PreRunConfig(TypedDict):
    contexts: list[Callable[[CapsuleParams], ContextBase] | ContextBase]
    reporters: list[Callable[[CapsuleParams], ReporterBase] | ReporterBase]


class _InRunConfig(TypedDict):
    watchers: list[Callable[[CapsuleParams], WatcherBase] | WatcherBase]
    reporters: list[Callable[[CapsuleParams], ReporterBase] | ReporterBase]


class _PostRunConfig(TypedDict):
    contexts: list[Callable[[CapsuleParams], ContextBase] | ContextBase]
    reporters: list[Callable[[CapsuleParams], ReporterBase] | ReporterBase]


_CapsulaConfig = TypedDict(
    "_CapsulaConfig",
    {
        "vault-dir": Optional[Path],
        "pre-run": _PreRunConfig,
        "in-run": _InRunConfig,
        "post-run": _PostRunConfig,
    },
)


def load_config(path: Path) -> _CapsulaConfig:
    with path.open("rb") as file:
        raw_config = tomllib.load(file)

    project_root = path.parent
    if "vault-dir" in raw_config:
        if Path(raw_config["vault-dir"]).is_absolute():
            vault_dir = Path(raw_config["vault-dir"])
        else:
            vault_dir = project_root / Path(raw_config["vault-dir"])
    else:
        vault_dir = None

    config: _CapsulaConfig = {
        "vault-dir": vault_dir,
        "pre-run": {"contexts": [], "reporters": []},
        "in-run": {"watchers": [], "reporters": []},
        "post-run": {"contexts": [], "reporters": []},
    }

    if (pre_run := raw_config.get("pre-run")) is not None:
        config["pre-run"]["contexts"] = list(map(_construct_context, pre_run.get("contexts", [])))
        config["pre-run"]["reporters"] = list(map(_construct_reporter, pre_run.get("reporters", [])))
    if (in_run := raw_config.get("in-run")) is not None:
        config["in-run"]["watchers"] = list(map(_construct_watcher, in_run.get("watchers", [])))
        config["in-run"]["reporters"] = list(map(_construct_reporter, in_run.get("reporters", [])))
    if (post_run := raw_config.get("post-run")) is not None:
        config["post-run"]["contexts"] = list(map(_construct_context, post_run.get("contexts", [])))
        config["post-run"]["reporters"] = list(map(_construct_reporter, post_run.get("reporters", [])))

    return config


if __name__ == "__main__":
    print(load_config(Path(__file__).parent.parent / "capsula.toml"))  # noqa: T201
