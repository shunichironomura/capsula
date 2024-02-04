from abc import ABC, abstractmethod

from capsula._capsule import Capsule


class ReporterBase(ABC):
    @abstractmethod
    def report(self, capsule: Capsule) -> None:
        raise NotImplementedError
