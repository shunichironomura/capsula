from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner

import capsula
from capsula.__main__ import main
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig

from .utils import temporary_root_directory


def test_empty_func() -> None:
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:

        @capsula.monitor(
            directory=Path(root_directory),
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
    ("cmd", "exit_code", "stdout", "stderr"),
    [
        (["true"], 0, "", None),
        (["false"], 1, "", None),
        pytest.param(
            ["echo", "hello"],
            0,
            "hello\n",
            None,
            marks=pytest.mark.xfail(
                reason="Now that we use subprocess.run, stdout/stderr are not passed to the parent process.",
            ),
        ),
    ],
)
def test_empty_cli(cmd: Iterable[str], exit_code: int, stdout: str | None, stderr: str | None) -> None:
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "monitor", "--", *cmd])
        assert result.exit_code == exit_code
        assert stdout is None or result.stdout == stdout
        assert stderr is None or result.stderr == stderr
