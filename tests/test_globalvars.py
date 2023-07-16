from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import capsula
from capsula.__main__ import main
from capsula._monitor import PostRunInfoCli
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig

from .utils import temporary_root_directory


def test_monitor_cli_capsule_name() -> None:
    vault_directory = Path("vault")
    capsule_template = "capsule"
    capsula_config = CapsulaConfig(
        vault_directory=vault_directory,
        capsule_template=capsule_template,
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )
    cmd = ["python", "-c", "import sys, os; sys.stdout.write(os.environ['CAPSULA_CAPSULE_NAME'])"]

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "monitor", "--", *cmd])
        assert result.exit_code == 0

        post_run_info_file = root_directory / vault_directory / capsule_template / "post-run-info.json"
        post_run_info = PostRunInfoCli(**json.loads(post_run_info_file.read_text()))
        assert post_run_info.exit_code == 0
        assert post_run_info.stdout == capsule_template
        assert post_run_info.stderr == ""


def test_monitor_func_capsule_name() -> None:
    vault_directory = Path("vault")
    capsule_template = "capsule"
    capsula_config = CapsulaConfig(
        vault_directory=vault_directory,
        capsule_template=capsule_template,
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:

        @capsula.monitor(
            directory=root_directory,
        )
        def func() -> None:
            assert capsula.get_capsule_name() == capsule_template

        func()


def test_monitor_func_capsule_dir() -> None:
    vault_directory = Path("vault")
    capsule_template = "capsule"
    capsula_config = CapsulaConfig(
        vault_directory=vault_directory,
        capsule_template=capsule_template,
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:

        @capsula.monitor(
            directory=root_directory,
        )
        def func() -> None:
            assert capsula.get_capsule_dir() == root_directory / vault_directory / capsule_template

        func()


def test_capsule_name_not_set() -> None:
    with pytest.raises(capsula.CapsulaConfigurationError):
        capsula.get_capsule_name()


def test_capsule_dir_not_set() -> None:
    with pytest.raises(capsula.CapsulaConfigurationError):
        capsula.get_capsule_dir()
