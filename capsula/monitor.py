from __future__ import annotations

import logging
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from capsula.capture import CaptureConfig
    from capsula.context import Context

logger = logging.getLogger(__name__)


class MonitorConfig(BaseModel):
    ...


class PreCLIRunInfo(BaseModel):
    timestamp: datetime
    cwd: Path
    args: list[str]


class PostCLIRunInfo(BaseModel):
    timestamp: datetime
    run_time: timedelta
    stdout: str
    stderr: str
    exit_code: int


def monitor_cli(
    args: Sequence[str],
    *,
    config: MonitorConfig,  # noqa: ARG001
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

    with (capture_config.capsule / "post-run-info.json").open("w") as f:
        f.write(post_run_info.model_dump_json(indent=4))

    return pre_run_info, post_run_info
