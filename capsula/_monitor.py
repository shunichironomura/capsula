from __future__ import annotations

import inspect
import logging
import subprocess
import sys
import time

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib
import traceback
import warnings
from abc import ABC, abstractmethod

if sys.version_info < (3, 11):
    from datetime import timezone as _timezone

    UTC = _timezone.utc
else:
    from datetime import UTC
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

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
    source_file: Path | None
    source_line: int | None
    function_name: str
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


class ExceptionInfo(BaseModel):
    error_type: str
    error_message: str
    error_details: str

    @classmethod
    def from_exception(cls, exc: BaseException) -> ExceptionInfo:
        return cls(
            error_type=type(exc).__name__,
            error_message=str(exc),
            error_details=traceback.format_exc(),
        )


class PostRunInfoFunc(PostRunInfoBase):
    return_value: Any | None = None
    exception_info: ExceptionInfo | None = None


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
    def run(
        self,
        pre_run_info: _TPreRunInfo,
        *,
        items: Iterable[str],
        **kwargs: Any,
    ) -> tuple[_TPostRunInfo, BaseException | None]:
        ...

    def run_and_teardown(
        self,
        pre_run_info: _TPreRunInfo,
        *,
        items: Iterable[str],
        **kwargs: Any,
    ) -> tuple[_TPostRunInfo, BaseException | None]:
        post_run_info, exc = self.run(pre_run_info, items=items, **kwargs)
        return self.teardown(post_run_info=post_run_info, items=items), exc

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

    def run(
        self,
        pre_run_info: PreRunInfoCli,
        *,
        items: Iterable[str],  # noqa: ARG002
    ) -> tuple[PostRunInfoCli, None]:
        start_time = time.perf_counter()
        result = subprocess.run(pre_run_info.args, capture_output=True, text=True)  # noqa: S603
        end_time = time.perf_counter()

        return (
            PostRunInfoCli(
                timestamp=datetime.now(UTC).astimezone(),
                run_time=timedelta(seconds=end_time - start_time),
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            ),
            None,
        )


class MonitoringHandlerFunc(MonitoringHandlerBase[PreRunInfoFunc, PostRunInfoFunc]):
    def setup_pre_run_info(
        self,
        func: Callable[..., Any],
        args: Sequence[Any],
        kwargs: dict[str, Any],
    ) -> PreRunInfoFunc:
        try:
            file_path = inspect.getsourcefile(func)
        except TypeError:
            file_path = None
        file_path = Path(file_path) if file_path is not None else None

        try:
            _, first_line_no = inspect.getsourcelines(func)
        except (TypeError, OSError):
            first_line_no = None

        return PreRunInfoFunc(
            cwd=Path.cwd(),
            timestamp=datetime.now(UTC).astimezone(),
            source_file=file_path,
            source_line=first_line_no,
            function_name=func.__name__,
            args=tuple(args),
            kwargs=kwargs,
        )

    def run(
        self,
        pre_run_info: PreRunInfoFunc,
        *,
        items: Iterable[str],  # noqa: ARG002
        func: Callable[..., Any],
    ) -> tuple[PostRunInfoFunc, BaseException | None]:
        start_time = time.perf_counter()
        try:
            ret = func(*pre_run_info.args, **pre_run_info.kwargs)
        except Exception as e:  # noqa: BLE001
            end_time = time.perf_counter()
            exception_info = ExceptionInfo.from_exception(e)
            return (
                PostRunInfoFunc(
                    timestamp=datetime.now(UTC).astimezone(),
                    run_time=timedelta(seconds=end_time - start_time),
                    exception_info=exception_info,
                ),
                e,
            )
        else:
            end_time = time.perf_counter()
            return (
                PostRunInfoFunc(
                    timestamp=datetime.now(UTC).astimezone(),
                    run_time=timedelta(seconds=end_time - start_time),
                    return_value=ret,
                ),
                None,
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

            pre_run_info = handler.setup(func=func, args=args, kwargs=kwargs)
            post_run_info, exc = handler.run_and_teardown(
                pre_run_info=pre_run_info,
                items=items,
                func=func,
            )
            if exc is not None:
                logger.error(f"Exception occurred: {exc!r}")
                raise exc

            ret = post_run_info.return_value

            if not include_return_value:
                post_run_info.return_value = None

            return ret  # type: ignore

        return wrapper

    return decorator
