from pathlib import Path

import pytest
from click.testing import CliRunner

from capsula.__main__ import main
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig

from .utils import temporary_root_directory


def test_capture() -> None:
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "capture"])
        assert result.exit_code == 0


@pytest.mark.parametrize(
    ("cmd", "exit_code"),
    [
        (
            'python -c "import sys; sys.exit(0)"',
            0,
        ),
        (
            'python -c "import sys; sys.exit(1)"',
            1,
        ),
    ],
)
def test_capture_pre_capture_command(cmd: str, exit_code: int) -> None:
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(
            pre_capture_commands=[cmd],
        ),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        runner = CliRunner()
        result = runner.invoke(main, ["--directory", str(root_directory), "capture"])
        assert (result.exit_code == 0) == (exit_code == 0)
