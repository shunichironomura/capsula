from __future__ import annotations

import logging
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Literal, ParamSpec, TypeVar

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from capsula.capture import CaptureConfig
    from capsula.context import Context
from capsula.file import CaptureFileConfig  # noqa: TCH001 for pydantic
from capsula.hash import compute_hash

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    files: dict[Path, CaptureFileConfig] = Field(default_factory=dict)


class PreCLIRunInfo(BaseModel):
    timestamp: datetime
    cwd: Path
    args: list[str]


class OutputFileInfo(BaseModel):
    hash_algorithm: Literal["md5", "sha1", "sha256", "sha3"]
    file_hash: str = Field(..., alias="hash")


class PostCLIRunInfo(BaseModel):
    timestamp: datetime
    run_time: timedelta
    stdout: str
    stderr: str
    exit_code: int
    files: dict[Path, OutputFileInfo | None] = Field(default_factory=dict)


def monitor_cli(
    args: Sequence[str],
    *,
    monitor_config: MonitorConfig,
    context: Context,  # noqa: ARG001
    capture_config: CaptureConfig,
) -> tuple[PreCLIRunInfo, PostCLIRunInfo]:
    pre_run_info = PreCLIRunInfo(args=list(args), cwd=Path.cwd(), timestamp=datetime.now(UTC).astimezone())

    with (capture_config.capsule / "pre-run-info.json").open("w") as f:
        f.write(pre_run_info.model_dump_json(indent=4))

    start_time = time.perf_counter()
    result = subprocess.run(args, capture_output=True, text=True)  # noqa: S603
    end_time = time.perf_counter()

    post_run_info = PostCLIRunInfo(
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


def monitor(fn: Callable[P, T]) -> Callable[P, T]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        logging.info(f"{fn.__name__} was called")
        return fn(*args, **kwargs)

    return inner
