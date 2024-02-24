from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, MutableMapping

from ._backport import tomllib
from ._context import ContextBase

if TYPE_CHECKING:
    from ._run import CapsuleParams


def _construct_context(raw_config: MutableMapping[str, Any]) -> Callable[[CapsuleParams], ContextBase] | ContextBase:
    context_class_name = raw_config.pop("type")
    context_class = ContextBase.get_subclass(context_class_name)
    return context_class.default(**raw_config)


def load_config(path: Path):
    with path.open("rb") as file:
        raw_config = tomllib.load(file)

    config = {
        "pre-run": {"context": [], "reporter": []},
        "in-run": {"watcher": [], "reporter": []},
        "post-run": {"context": [], "reporter": []},
    }

    if (pre_run := raw_config.get("pre-run")) is not None:
        config["pre-run"]["context"] = [_construct_context(conf) for conf in pre_run.get("context", [])]

    print(config)


if __name__ == "__main__":
    load_config(Path(__file__).parent.parent / "capsula.toml")
