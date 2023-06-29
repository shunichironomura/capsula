from __future__ import annotations

import logging
import subprocess
import time
import tomllib
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, TypeVar

from pydantic import BaseModel, Field

from capsula.capture import capture as capture_core

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from capsula.context import Context
from capsula.capture import CaptureConfig
from capsula.file import CaptureFileConfig  # noqa: TCH001 for pydantic
from capsula.hash import compute_hash

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)


class PreRunInfo(BaseModel):
    timestamp: datetime
    cwd: Path
    args: list[str] | None = None


class OutputFileInfo(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"]
    file_hash: str = Field(..., alias="hash")


class PostRunInfo(BaseModel):
    timestamp: datetime
    run_time: timedelta
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    return_value: Any | None = None
    files: dict[Path, OutputFileInfo | None] = Field(default_factory=dict)


def monitor_cli(
    args: Sequence[str],
    *,
    monitor_config: MonitorConfig,
    context: Context,  # noqa: ARG001
    capture_config: CaptureConfig,
) -> tuple[PreRunInfo, PostRunInfo]:
    pre_run_info = PreRunInfo(args=list(args), cwd=Path.cwd(), timestamp=datetime.now(UTC).astimezone())

    with (capture_config.capsule / "pre-run-info.json").open("w") as f:
        f.write(pre_run_info.model_dump_json(indent=4))

    start_time = time.perf_counter()
    result = subprocess.run(args, capture_output=True, text=True)  # noqa: S603
    end_time = time.perf_counter()

    post_run_info = PostRunInfo(
        timestamp=datetime.now(UTC).astimezone(),
        run_time=timedelta(seconds=end_time - start_time),
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )

    files = {}
    for path, file in monitor_config.files.items():
        if not path.exists():
            files[path] = None
            continue
        files[path] = OutputFileInfo(
            hash_algorithm=file.hash_algorithm,
            hash=compute_hash(path, file.hash_algorithm),
        )
        if file.copy_:
            copyfile(path, capture_config.capsule / path.name)

    post_run_info.files = files

    with (capture_config.capsule / "post-run-info.json").open("w") as f:
        f.write(post_run_info.model_dump_json(indent=4))

    return pre_run_info, post_run_info


T = TypeVar("T")
P = ParamSpec("P")


def monitor(
    directory: Path,
    *,
    include_return_value: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
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

            pre_run_info = PreRunInfo(cwd=Path.cwd(), timestamp=datetime.now(UTC).astimezone())
            with (capture_config.capsule / "pre-run-info.json").open("w") as f:
                f.write(pre_run_info.model_dump_json(indent=4))

            start_time = time.perf_counter()
            ret = func(*args, **kwargs)
            end_time = time.perf_counter()

            post_run_info = PostRunInfo(
                timestamp=datetime.now(UTC).astimezone(),
                run_time=timedelta(seconds=end_time - start_time),
            )

            if include_return_value:
                post_run_info.return_value = ret

            files = {}
            for path, file in monitor_config.files.items():
                if not path.exists():
                    files[path] = None
                    continue
                files[path] = OutputFileInfo(
                    hash_algorithm=file.hash_algorithm,
                    hash=compute_hash(path, file.hash_algorithm),
                )
                if file.copy_:
                    copyfile(path, capture_config.capsule / path.name)

            post_run_info.files = files

            with (capture_config.capsule / "post-run-info.json").open("w") as f:
                f.write(post_run_info.model_dump_json(indent=4))

            return ret

        return wrapper

    return decorator
