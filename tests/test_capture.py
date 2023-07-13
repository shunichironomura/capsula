import tempfile
from pathlib import Path

from capsula.capture import capture
from capsula.config import CapsulaConfig, CaptureConfig, MonitorConfig


def test_capture() -> None:
    with tempfile.TemporaryDirectory() as root_directory:
        capsula_config = CapsulaConfig(
            vault_directory=Path(root_directory) / "vault",
            capsule_template=r"%Y%m%d_%H%M%S",
            capture=CaptureConfig(),
            monitor=MonitorConfig(),
        )
        capsula_config.root_directory = Path(root_directory)

        ctx = capture(config=capsula_config)

        assert ctx.platform is not None
        assert ctx.cpu is not None
        assert ctx.environment_variables == {}
        assert ctx.cwd == Path.cwd()
