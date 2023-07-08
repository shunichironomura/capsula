import tempfile
from pathlib import Path

from capsula.capture import CaptureConfig, capture


def test_capture() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        capture_config = CaptureConfig(
            vault_directory=Path(tempdir),
            capsule_template=r"%Y%m%d_%H%M%S",
        )

        ctx = capture(config=capture_config)

        assert ctx.platform is not None
        assert ctx.cpu is not None
        assert ctx.environment_variables == {}
        assert ctx.cwd == Path.cwd()
