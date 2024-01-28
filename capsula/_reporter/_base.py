from abc import ABC, abstractmethod

from capsula.encapsulator import Capsule


class ReporterBase(ABC):
    @abstractmethod
    def report(self, capsule: Capsule) -> None:
        raise NotImplementedError
