from abc import ABC, abstractmethod

class HolographicInterface(ABC):
    @abstractmethod
    def holographic_entropy(self) -> float:
        """Calculate holographic entropy."""
        pass
