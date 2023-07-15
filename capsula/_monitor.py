import inspect
import logging
import subprocess
import sys
import time
import traceback
import warnings
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from shutil import copyfile, move
from typing import Any, Callable, Dict, Generic, Iterable, List, Mapping, Optional, Sequence, Tuple, TypeVar

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

if sys.version_info < (3, 11):
    from datetime import datetime, timedelta
    from datetime import timezone as _timezone

    UTC = _timezone.utc
else:
    from datetime import UTC, datetime, timedelta

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from pydantic import BaseModel, Field

from capsula.capture import capture as capture_core
from capsula.config import CapsulaConfig
from capsula.hash import HashAlgorithm, compute_hash

logger = logging.getLogger(__name__)


class PreRunInfoBase(BaseModel):
    root_directory: Path
    cwd: Path = Field(default_factory=Path.cwd)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC).astimezone())


class PreRunInfoCli(PreRunInfoBase):
    args: List[str]


class PreRunInfoFunc(PreRunInfoBase):
    source_file: Optional[Path]
    source_line: Optional[int]
    function_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


class OutputFileInfo(BaseModel):
    hash_algorithm: Optional[HashAlgorithm]
    file_hash: Optional[str] = Field(..., alias="hash")


class PostRunInfoBase(BaseModel):
    root_directory: Path
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC).astimezone())
    run_time: timedelta
    files: Dict[Path, Optional[OutputFileInfo]] = Field(default_factory=dict)


class PostRunInfoCli(PostRunInfoBase):
    stdout: str
    stderr: str
    exit_code: int


class ExceptionInfo(BaseModel):
    error_type: str
    error_message: str
    error_details: str

    @classmethod
    def from_exception(cls, exc: BaseException) -> "ExceptionInfo":
        return cls(
            error_type=type(exc).__name__,
            error_message=str(exc),
            error_details=traceback.format_exc(),
        )


class PostRunInfoFunc(PostRunInfoBase):
    return_value: Optional[Any] = None
    exception_info: Optional[ExceptionInfo] = None


_TPreRunInfo = TypeVar("_TPreRunInfo", bound=PreRunInfoBase)
_TPostRunInfo = TypeVar("_TPostRunInfo", bound=PostRunInfoBase)


class MonitoringHandlerBase(ABC, Generic[_TPreRunInfo, _TPostRunInfo]):
    def __init__(self, *, config: CapsulaConfig) -> None:
        self.config = config

    @abstractmethod
    def setup_pre_run_info(self, *args: Any, **kwargs: Any) -> _TPreRunInfo:
        ...

    def setup(self, *args: Any, **kwargs: Any) -> _TPreRunInfo:
        """Setup the pre-run info and dump it to a file."""
        pre_run_info = self.setup_pre_run_info(*args, **kwargs)
        self.dump_pre_run_info(pre_run_info)
        return pre_run_info

    def dump_pre_run_info(self, pre_run_info: _TPreRunInfo) -> None:
        with (self.config.capsule / "pre-run-info.json").open("w") as f:
            f.write(pre_run_info.model_dump_json(indent=4))

    @abstractmethod
    def run(
        self,
        pre_run_info: _TPreRunInfo,
        *,
        items: Iterable[str],
        **kwargs: Any,
    ) -> Tuple[_TPostRunInfo, Optional[BaseException]]:
        ...

    def run_and_teardown(
        self,
        pre_run_info: _TPreRunInfo,
        *,
        items: Iterable[str],
        **kwargs: Any,
    ) -> Tuple[_TPostRunInfo, Optional[BaseException]]:
        post_run_info, exc = self.run(pre_run_info, items=items, **kwargs)
        return self.teardown(post_run_info=post_run_info, items=items), exc

    def teardown(self, post_run_info: _TPostRunInfo, *, items: Iterable[str]) -> _TPostRunInfo:
        post_run_info.files = {}
        for item in items:
            for relative_path, file in self.config.monitor.items[item].files.items():
                logger.debug(f"Capturing file {relative_path}...")
                path = self.config.root_directory / relative_path
                if not path.exists():
                    logger.warning(f"File {relative_path} does not exist.")
                    post_run_info.files[relative_path] = None
                    continue
                post_run_info.files[relative_path] = OutputFileInfo(
                    hash_algorithm=file.hash_algorithm,
                    hash=compute_hash(path, file.hash_algorithm) if file.hash_algorithm else None,
                )
                if file.copy_:
                    copyfile(path, self.config.capsule / path.name)
                elif file.move:
                    move(path, self.config.capsule / path.name)

        with (self.config.capsule / "post-run-info.json").open("w") as f:
            f.write(post_run_info.model_dump_json(indent=4))

        return post_run_info


class MonitoringHandlerCli(MonitoringHandlerBase[PreRunInfoCli, PostRunInfoCli]):
    def setup_pre_run_info(self, args: Sequence[str]) -> PreRunInfoCli:
        return PreRunInfoCli(
            root_directory=self.config.root_directory,
            args=list(args),
            cwd=Path.cwd(),
            timestamp=datetime.now(UTC).astimezone(),
        )

    def run(
        self,
        pre_run_info: PreRunInfoCli,
        *,
        items: Iterable[str],  # noqa: ARG002
        **_: Any,  # to be compatible with the base class
    ) -> Tuple[PostRunInfoCli, None]:
        start_time = time.perf_counter()
        result = subprocess.run(pre_run_info.args, capture_output=True, text=True)  # noqa: S603
        end_time = time.perf_counter()

        return (
            PostRunInfoCli(
                root_directory=self.config.root_directory,
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
        kwargs: Mapping[str, Any],
    ) -> PreRunInfoFunc:
        try:
            _file_path_str = inspect.getsourcefile(func)
        except TypeError:
            _file_path_str = None
        file_path = Path(_file_path_str) if _file_path_str is not None else None

        try:
            _, first_line_no = inspect.getsourcelines(func)
        except (TypeError, OSError):
            first_line_no = None

        return PreRunInfoFunc(
            root_directory=self.config.root_directory,
            cwd=Path.cwd(),
            timestamp=datetime.now(UTC).astimezone(),
            source_file=file_path,
            source_line=first_line_no,
            function_name=func.__name__,
            args=tuple(args),
            kwargs=dict(kwargs),
        )

    def run(  # type: ignore[override]  # `func` is added to the signature
        self,
        pre_run_info: PreRunInfoFunc,
        *,
        items: Iterable[str],  # noqa: ARG002
        func: Callable[..., Any],
        **_: Any,  # to be compatible with the base class
    ) -> Tuple[PostRunInfoFunc, Optional[BaseException]]:
        start_time = time.perf_counter()
        try:
            ret = func(*pre_run_info.args, **pre_run_info.kwargs)
        except Exception as e:  # noqa: BLE001
            end_time = time.perf_counter()
            exception_info = ExceptionInfo.from_exception(e)
            return (
                PostRunInfoFunc(
                    root_directory=self.config.root_directory,
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
                    root_directory=self.config.root_directory,
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
            config = CapsulaConfig(**tomllib.load(capsula_config_file))
        config.root_directory = directory

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            config.ensure_capsule_directory_exists()
            if config.monitor.capture:
                captured_ctx = capture_core(config=config)
                logger.debug(f"Captured context: {captured_ctx}")

            handler = MonitoringHandlerFunc(config=config)

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
