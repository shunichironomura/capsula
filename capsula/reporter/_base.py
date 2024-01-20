from abc import ABC, abstractmethod

from capsula.encapsulator import Capsule


class Reporter(ABC):
    @abstractmethod
    def report(self, capsule: Capsule) -> None:
        ...
