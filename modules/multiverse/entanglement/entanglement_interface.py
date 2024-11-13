from abc import ABC, abstractmethod
import numpy as np

class EntanglementInterface(ABC):
    @abstractmethod
    def calculate_entropy(self, density_matrix: np.ndarray) -> float:
        """Calculate entanglement entropy."""
        pass
