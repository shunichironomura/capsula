from __future__ import annotations

import logging
import subprocess
import time
import tomllib
import warnings
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Any, Generic, Literal, ParamSpec, TypeVar

from pydantic import BaseModel, Field

from capsula.capture import CaptureConfig
from capsula.capture import capture as capture_core
from capsula.file import CaptureFileConfig  # noqa: TCH001 for pydantic
from capsula.hash import compute_hash

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


logger = logging.getLogger(__name__)


class MonitorItemConfig(BaseModel):
    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)


class MonitorConfig(BaseModel):
    items: dict[str, MonitorItemConfig] = Field(default_factory=dict, alias="item")


class PreRunInfoBase(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC).astimezone())
    cwd: Path = Field(default_factory=Path.cwd)


class PreRunInfoCli(PreRunInfoBase):
    args: list[str]


class PreRunInfoFunc(PreRunInfoBase):
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class OutputFileInfo(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"]
    file_hash: str = Field(..., alias="hash")


class PostRunInfoBase(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC).astimezone())
    run_time: timedelta
    files: dict[Path, OutputFileInfo | None] = Field(default_factory=dict)


class PostRunInfoCli(PostRunInfoBase):
    stdout: str
    stderr: str
    exit_code: int


class PostRunInfoFunc(PostRunInfoBase):
    return_value: Any


_TPreRunInfo = TypeVar("_TPreRunInfo", bound=PreRunInfoBase)
_TPostRunInfo = TypeVar("_TPostRunInfo", bound=PostRunInfoBase)


class MonitoringHandlerBase(ABC, Generic[_TPreRunInfo, _TPostRunInfo]):
    def __init__(self, *, capture_config: CaptureConfig, monitor_config: MonitorConfig) -> None:
        self.capture_config = capture_config
        self.monitor_config = monitor_config

    @abstractmethod
    def setup_pre_run_info(self, *args: Any, **kwargs: Any) -> _TPreRunInfo:
        ...

    def setup(self, *args: Any, **kwargs: Any) -> _TPreRunInfo:
        """Setup the pre-run info and dump it to a file."""
        pre_run_info = self.setup_pre_run_info(*args, **kwargs)
        self.dump_pre_run_info(pre_run_info)
        return pre_run_info

    def dump_pre_run_info(self, pre_run_info: _TPreRunInfo) -> None:
        with (self.capture_config.capsule / "pre-run-info.json").open("w") as f:
            f.write(pre_run_info.model_dump_json(indent=4))

    @abstractmethod
    def run(self, pre_run_info: _TPreRunInfo, *, items: Iterable[str], **kwargs: Any) -> _TPostRunInfo:
        ...

    def run_and_teardown(self, pre_run_info: _TPreRunInfo, *, items: Iterable[str], **kwargs: Any) -> _TPostRunInfo:
        post_run_info = self.run(pre_run_info, items=items, **kwargs)
        return self.teardown(post_run_info=post_run_info, items=items)

    def teardown(self, post_run_info: _TPostRunInfo, *, items: Iterable[str]) -> _TPostRunInfo:
        post_run_info.files = {}
        for item in items:
            for path, file in self.monitor_config.items[item].files.items():
                logger.debug(f"Capturing file {path}...")
                if not path.exists():
                    logger.warning(f"File {path} does not exist.")
                    post_run_info.files[path] = None
                    continue
                post_run_info.files[path] = OutputFileInfo(
                    hash_algorithm=file.hash_algorithm,
                    hash=compute_hash(path, file.hash_algorithm),
                )
                if file.copy_:
                    copyfile(path, self.capture_config.capsule / path.name)

        with (self.capture_config.capsule / "post-run-info.json").open("w") as f:
            f.write(post_run_info.model_dump_json(indent=4))

        return post_run_info


class MonitoringHandlerCli(MonitoringHandlerBase[PreRunInfoCli, PostRunInfoCli]):
    def setup_pre_run_info(self, args: Sequence[str]) -> PreRunInfoCli:
        return PreRunInfoCli(args=list(args), cwd=Path.cwd(), timestamp=datetime.now(UTC).astimezone())

    def run(self, pre_run_info: PreRunInfoCli, *, items: Iterable[str]) -> PostRunInfoCli:
        start_time = time.perf_counter()
        result = subprocess.run(pre_run_info.args, capture_output=True, text=True)  # noqa: S603
        end_time = time.perf_counter()

        return PostRunInfoCli(
            timestamp=datetime.now(UTC).astimezone(),
            run_time=timedelta(seconds=end_time - start_time),
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )


class MonitoringHandlerFunc(MonitoringHandlerBase[PreRunInfoFunc, PostRunInfoFunc]):
    def setup_pre_run_info(self, *args: Any, **kwargs: Any) -> PreRunInfoFunc:
        return PreRunInfoFunc(
            cwd=Path.cwd(),
            timestamp=datetime.now(UTC).astimezone(),
            args=args,
            kwargs=kwargs,
        )

    def run(
        self,
        pre_run_info: PreRunInfoFunc,
        *,
        items: Iterable[str],
        func: Callable[..., Any],
    ) -> PostRunInfoFunc:
        start_time = time.perf_counter()
        ret = func(*pre_run_info.args, **pre_run_info.kwargs)
        end_time = time.perf_counter()

        return PostRunInfoFunc(
            timestamp=datetime.now(UTC).astimezone(),
            run_time=timedelta(seconds=end_time - start_time),
            return_value=ret,
        )


T = TypeVar("T")
P = ParamSpec("P")


def monitor(
    directory: Path,
    *,
    items: Iterable[str] = (),
    include_return_value: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    if isinstance(items, str):
        warnings.warn(
            "Passing a single string to `monitor` is deprecated. Use a tuple instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        items = (items,)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        capsula_config_path = directory / "capsula.toml"
        with capsula_config_path.open("rb") as capsula_config_file:
            capsula_config = tomllib.load(capsula_config_file)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            capture_config = CaptureConfig(**capsula_config["capture"])
            captured_ctx = capture_core(config=capture_config)
            logger.debug(f"Captured context: {captured_ctx}")

            monitor_config = MonitorConfig(**capsula_config["monitor"])
            logger.debug(f"Monitor config: {monitor_config}")

            handler = MonitoringHandlerFunc(capture_config=capture_config, monitor_config=monitor_config)

            pre_run_info = handler.setup(*args, **kwargs)
            post_run_info = handler.run_and_teardown(
                pre_run_info=pre_run_info,
                items=items,
                func=func,
            )

            ret = post_run_info.return_value

            if not include_return_value:
                post_run_info.return_value = None

            return ret

        return wrapper

    return decorator
