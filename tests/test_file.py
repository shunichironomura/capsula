from __future__ import annotations

from pathlib import Path

import pytest

import capsula
from capsula.config import CapsulaConfig, CaptureConfig, CaptureFileConfig, MonitorConfig

from .utils import temporary_root_directory


def test_file_copy() -> None:
    file_name = "test.txt"
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(
            files={
                Path(file_name): CaptureFileConfig(
                    copy=True,
                ),
            },
        ),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        test_file = root_directory / file_name
        test_file.write_text("Hello, world!")

        @capsula.monitor(
            directory=root_directory,
        )
        def func() -> None:
            pass

        func()
        vault_dir = root_directory / "vault"

        # Find the capsule directory
        capsule_dir = vault_dir / next(vault_dir.iterdir())
        copied_file = capsule_dir / file_name
        assert test_file.is_file()
        assert copied_file.is_file()
        assert test_file.read_text() == copied_file.read_text()


def test_file_move() -> None:
    file_name = "test.txt"
    capsula_config = CapsulaConfig(
        vault_directory=Path("vault"),
        capsule_template=r"%Y%m%d_%H%M%S",
        capture=CaptureConfig(
            files={
                Path(file_name): CaptureFileConfig(
                    move=True,
                ),
            },
        ),
        monitor=MonitorConfig(),
    )

    with temporary_root_directory(capsula_config) as root_directory:
        test_file = root_directory / file_name
        test_file.write_text("Hello, world!")
        file_content = test_file.read_text()

        @capsula.monitor(
            directory=root_directory,
        )
        def func() -> None:
            pass

        func()
        vault_dir = root_directory / "vault"

        # Find the capsule directory
        capsule_dir = vault_dir / next(vault_dir.iterdir())
        copied_file = capsule_dir / file_name
        assert not test_file.is_file()
        assert copied_file.is_file()
        assert copied_file.read_text() == file_content


def test_file_copy_and_move() -> None:
    file_name = "test.txt"
    with pytest.raises(ValueError, match="Only one of `copy` or `move` can be set"):
        CapsulaConfig(
            vault_directory=Path("vault"),
            capsule_template=r"%Y%m%d_%H%M%S",
            capture=CaptureConfig(
                files={
                    Path(file_name): CaptureFileConfig(
                        move=True,
                        copy=True,
                    ),
                },
            ),
            monitor=MonitorConfig(),
        )
