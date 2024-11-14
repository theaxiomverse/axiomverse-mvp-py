from abc import ABC, abstractmethod
import numpy as np

class ProjectionInterface(ABC):
    @abstractmethod
    def project(self, vector: np.ndarray, target_dim: int) -> np.ndarray:
        """Project a vector onto a lower-dimensional space."""
        pass
