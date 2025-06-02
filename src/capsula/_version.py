import importlib.metadata
from typing import Annotated

from typing_extensions import Doc

__version__: Annotated[str, Doc("Capsula version.")] = importlib.metadata.version("capsula")
