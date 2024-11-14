from abc import ABC, abstractmethod
import numpy as np

class GaugeTransformationInterface(ABC):
    @abstractmethod
    def apply_transformation(self, data_vector: np.ndarray) -> np.ndarray:
        """Apply a gauge transformation for secure data access."""
        pass

    @abstractmethod
    def reverse_transformation(self, transformed_vector: np.ndarray) -> np.ndarray:
        """Reverse the gauge transformation to retrieve original data."""
        pass
