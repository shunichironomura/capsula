from __future__ import annotations

from typing import Any, Final

from capsula._capsule import CapsuleItem


class ContextBase(CapsuleItem):
    _subclass_registry: Final[dict[str, type[ContextBase]]] = {}

    @property
    def abort_on_error(self) -> bool:
        return False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if cls.__name__ in cls._subclass_registry:
            msg = f"Duplicate context name: {cls.__name__}"
            raise ValueError(msg)
        cls._subclass_registry[cls.__name__] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def get_subclass(cls, name: str) -> type[ContextBase]:
        return cls._subclass_registry[name]
