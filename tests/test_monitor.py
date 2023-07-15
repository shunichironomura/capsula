import json
import tempfile
from pathlib import Path

import tomli_w

import capsula
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig


def test_monitor_func() -> None:
    with tempfile.TemporaryDirectory() as root_directory:
        capsula_config = CapsulaConfig(
            vault_directory=Path(root_directory) / "vault",
            capsule_template=r"%Y%m%d_%H%M%S",
            capture=CaptureConfig(),
            monitor=MonitorConfig(),
        )
        with (Path(root_directory) / "capsula.toml").open("wb") as f:
            json_str = capsula_config.model_dump_json()
            tomli_w.dump(json.loads(json_str), f)

        @capsula.monitor(
            directory=Path(root_directory),
        )
        def func() -> None:
            pass

        func()
