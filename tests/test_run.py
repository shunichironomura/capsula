import logging

import capsula

logger = logging.getLogger(__name__)


def test_default_run_dir() -> None:
    @capsula.run(ignore_config=True)
    def f(x: int, y: int) -> int:
        logger.info(f"Run directory: {capsula.Run.get_current().run_dir}")
        return x + y

    f(1, 2)
