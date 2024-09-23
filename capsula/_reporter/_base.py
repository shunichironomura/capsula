from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Final

if TYPE_CHECKING:
    from capsula._backport import Self
    from capsula._capsule import Capsule
    from capsula._run import CapsuleParams


class ReporterBase(ABC):
    _subclass_registry: Final[dict[str, type[ReporterBase]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if cls.__name__ in cls._subclass_registry:
            msg = f"Duplicate reporter name: {cls.__name__}"
            raise ValueError(msg)
        cls._subclass_registry[cls.__name__] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def get_subclass(cls, name: str) -> type[ReporterBase]:
        return cls._subclass_registry[name]

    @abstractmethod
    def report(self, capsule: Capsule) -> None:
        raise NotImplementedError

    @classmethod
    def builder(cls, *args: Any, **kwargs: Any) -> Callable[[CapsuleParams], Self]:
        def build(params: CapsuleParams) -> Self:  # type: ignore[type-var,misc] # noqa: ARG001
            return cls(*args, **kwargs)

        return build
