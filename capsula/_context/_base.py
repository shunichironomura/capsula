from __future__ import annotations

from typing import Any, Final

from capsula._capsule import CapsuleItem


class ContextBase(CapsuleItem):
    _subclass_registry: Final[dict[str, type[ContextBase]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls._subclass_registry[cls.__name__] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def get_subclass(cls, name: str) -> type[ContextBase]:
        return cls._subclass_registry[name]
