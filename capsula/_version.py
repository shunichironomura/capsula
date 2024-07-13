import importlib.metadata

from typing_extensions import Annotated, Doc

__version__: Annotated[str, Doc("Capsula version.")] = importlib.metadata.version("capsula")
