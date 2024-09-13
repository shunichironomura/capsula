import logging

import capsula

logger = logging.getLogger(__name__)


def test_default_run_dir() -> None:
    @capsula.run(ignore_config=True)
    def f(x: int, y: int) -> int:
        return x + y

    logger.info(f"Run directory: {f.run_dir}")
