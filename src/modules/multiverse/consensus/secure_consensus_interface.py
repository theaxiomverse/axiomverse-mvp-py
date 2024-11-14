from abc import ABC, abstractmethod
import numpy as np

class SecureConsensusInterface(ABC):
    @abstractmethod
    def secure_data(self, data_vector: np.ndarray) -> np.ndarray:
        """Apply security transformation to data."""
        pass

    @abstractmethod
    def verify_data(self, secured_vector: np.ndarray, original_vector: np.ndarray) -> bool:
        """Verify integrity of secured data."""
        pass
