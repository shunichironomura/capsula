import os
from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _reset_environment_variables() -> Iterator[None]:
    """Reset environment variables after each test."""
    yield

    for key in list(os.environ.keys()):
        if key.startswith("CAPSULA_"):
            del os.environ[key]
