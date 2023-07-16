from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner

import capsula
from capsula.__main__ import main
from capsula._monitor import PostRunInfoCli
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig

from .utils import temporary_root_directory


def test_monitor_empty_func() -> None:
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:

        @capsula.monitor(
            directory=root_directory,
        )
        def func() -> None:
            pass

        func()
        vault_dir = root_directory / "vault"
        assert vault_dir.is_dir()

        # Find the capsule directory
        capsule_dir = vault_dir / next(vault_dir.iterdir())
        assert capsule_dir.is_dir()
        context_file = capsule_dir / "context.json"
        assert context_file.is_file()


@pytest.mark.parametrize(
    ("cmd", "exit_code"),
    [
        pytest.param(
            ["true"],
            0,
            marks=pytest.mark.skipif(sys.platform == "win32", reason="Windows doesn't support true"),
        ),
        pytest.param(
            ["false"],
            1,
            marks=pytest.mark.skipif(sys.platform == "win32", reason="Windows doesn't support true"),
        ),
    ],
)
def test_monitor_cli_empty(cmd: Iterable[str], exit_code: int) -> None:
    vault_directory = Path("vault")
    capsula_config = CapsulaConfig(
        vault_directory=vault_directory,
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "monitor", "--", *cmd])
        assert result.exit_code == exit_code


@pytest.mark.parametrize(
    ("cmd", "exit_code", "stdout", "stderr"),
    [
        (
            ["python", "-c", "import sys; sys.exit(0)"],
            0,
            "",
            "",
        ),
        (
            ["python", "-c", "import sys; sys.exit(1)"],
            1,
            "",
            "",
        ),
        (
            ["python", "-c", "import sys; sys.stdout.write('hello\\n'); sys.stderr.write('world\\n')"],
            0,
            "hello\n",
            "world\n",
        ),
    ],
)
def test_monitor_cli(cmd: Iterable[str], exit_code: int, stdout: str, stderr: str) -> None:
    vault_directory = Path("vault")
    capsule_template = "capsule"
    capsula_config = CapsulaConfig(
        vault_directory=vault_directory,
        capsule_template=capsule_template,
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "monitor", "--", *cmd])
        assert result.exit_code == exit_code

        post_run_info_file = root_directory / vault_directory / capsule_template / "post-run-info.json"
        post_run_info = PostRunInfoCli(**json.loads(post_run_info_file.read_text()))
        assert post_run_info.exit_code == exit_code
        assert post_run_info.stdout == stdout
        assert post_run_info.stderr == stderr
