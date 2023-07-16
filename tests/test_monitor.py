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
    ("cmd", "exit_code"),
    [
        (["true"], 0),
        (["false"], 1),
    ],
)
def test_empty_cli(cmd: Iterable[str], exit_code: int) -> None:
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
