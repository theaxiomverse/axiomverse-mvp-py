import numpy as np
from ..security.gauge_transformation import GaugeTransformation
from ..consensus.secure_consensus_interface import SecureConsensusInterface

class SecureConsensusLayer(SecureConsensusInterface):
    def __init__(self, dimension):
        self.gauge_transformation = GaugeTransformation(dimension)

    def secure_data(self, data_vector: np.ndarray) -> np.ndarray:
        return self.gauge_transformation.apply_transformation(data_vector)

    def verify_data(self, recovered_vector: np.ndarray, original_vector: np.ndarray) -> bool:
        # Adjust dimensions if there's a mismatch
        if recovered_vector.shape != original_vector.shape:
            # If recovered_vector has fewer dimensions, pad it with zeros
            if recovered_vector.shape[0] < original_vector.shape[0]:
                recovered_vector = np.pad(recovered_vector, (0, original_vector.shape[0] - recovered_vector.shape[0]))
            # If recovered_vector has more dimensions, truncate it
            elif recovered_vector.shape[0] > original_vector.shape[0]:
                recovered_vector = recovered_vector[:original_vector.shape[0]]

        return np.allclose(recovered_vector, original_vector, rtol=1e-5, atol=1e-8)
