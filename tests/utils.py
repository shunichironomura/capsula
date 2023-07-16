import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import tomli_w

from capsula.config import CapsulaConfig


@contextmanager
def temporary_root_directory(capsula_config: CapsulaConfig) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as root_directory:
        with (Path(root_directory) / "capsula.toml").open("wb") as f:
            json_str = capsula_config.model_dump_json()
            tomli_w.dump(json.loads(json_str), f)
        yield Path(root_directory)
