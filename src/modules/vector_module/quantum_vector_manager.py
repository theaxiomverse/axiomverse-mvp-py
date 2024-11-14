from logging import error

import numpy as np
import time
from typing import Dict, List, Optional, Tuple
import logging
from .interfaces.vector_interface import VectorInterface
from .transaction_vector import TransactionVector
from .transaction_matrix import TransactionMatrix
from .transaction_layer import TransactionLayer
from .vss_utils import VSS  # Import VSS for secret sharing
from ..multiverse.security.gauge_transformation import GaugeTransformation
from ..multiverse.projection.dimensional_projections import DimensionalProjection
from ..multiverse.entanglement.entanglement_entropy import EntanglementEntropy
from ..multiverse.holography.holographic_screen import HolographicScreen
from ..multiverse.consensus.secure_consensus_layer import SecureConsensusLayer

logger = logging.getLogger(__name__)

class QuantumVectorManager:
    def __init__(self, threshold: int = 3, num_shares: int = 5, dimension: int = 5, target_dim: int = 3, area: float = 100.0):
        # Initialize a dictionary to store vectors by their IDs
        self.vectors: Dict[str, TransactionVector] = {}
        self.vss = VSS()  # Initialize VSS for secure secret sharing
        self.threshold = threshold  # Minimum number of shares for reconstruction
        self.num_shares = num_shares  # Total number of shares for each vector
        self.dimension = dimension
        self.target_dim = target_dim
        self.area = area

        # Initialize components for each enhancement
        self.gauge_transformation = GaugeTransformation(dimension)
        self.projection = DimensionalProjection(dimension)
        self.entanglement_entropy = EntanglementEntropy()
        self.holographic_screen = HolographicScreen(area)
        self.secure_consensus = SecureConsensusLayer(dimension)

        logger.info("QuantumVectorManager initialized with VSS, gauge transformations, and advanced features.")

    def create_vector(self, vector_id: str, coordinates: List[float]) -> TransactionVector | None:
        # Check for existing vector ID
        if vector_id in self.vectors:
            #logger.warning(f"Vector ID '{vector_id}' already exists. Creation aborted.")
            raise Exception(f"Vector ID '{vector_id}' already exists. Creation aborted.")# Return the existing vector or handle it differently

                 # Normalize the input coordinates and create a new vector
        normalized_coords = np.array(coordinates) / np.linalg.norm(coordinates)
        new_vector = TransactionVector()
        new_vector.add_layer("Coordinates", normalized_coords)
        new_vector.add_layer("State", {
            "state": "SUPERPOSITION", "coherence": 1.0, "energy": 1.0, "timestamp": time.time()
        })

        # Store the new vector in the dictionary
        self.vectors[vector_id] = new_vector
        logger.info(f"Vector {vector_id} created with initial state.")
        return new_vector

    # Inside QuantumVectorManager

    # QuantumVectorManager's secure_split_vector method
    def secure_split_vector(self, vector_id: str) -> List[List[Tuple[int, bytes, bytes, bytes]]]:
        """
        Securely split the vector coordinates for a specific vector by its ID.

        Parameters:
            vector_id (str): The ID of the vector to split.

        Returns:
            List of shares for each coordinate.
        """
        # Retrieve vector and serialize coordinates
        vector = self.get_vector(vector_id)
        if vector is None:
            logger.error(f"Vector {vector_id} not found.")
            return []

        # Retrieve and validate coordinates layer
        vector_data = vector.get_layer("Coordinates")
        print(vector_data)

        # Split the coordinates securely, regardless of dimensionality
        shares = self.vss.split_secret(vector_data, self.threshold, self.num_shares)
        logger.info(f"Vector {vector_id} split into {self.num_shares} shares with threshold {self.threshold}.")
        return shares

    def secure_reconstruct_vector(self, vector_id: str, shares: List[Tuple[int, bytes, bytes, bytes]]) -> bool:
        """Reconstruct vector data from shares and update the vector's state."""
        public_key = self.vss.falcon_public_key
        try:
            reconstructed_data = self.vss.reconstruct_secret(shares, public_key)
            reconstructed_coords = np.frombuffer(reconstructed_data, dtype=float)

            if vector_id in self.vectors:
                self.vectors[vector_id].add_layer("Coordinates", reconstructed_coords)
                logger.info(f"Vector {vector_id} successfully reconstructed.")
                return True
            else:
                logger.error(f"Vector {vector_id} does not exist.")
                return False
        except ValueError as e:
            logger.error(f"Failed to reconstruct vector {vector_id}: {e}")
            return False

    def update_vector(self, vector_id: str, new_coordinates: List[float], new_state: dict) -> bool:
        if vector_id not in self.vectors:
            logger.error(f"Vector {vector_id} not found")
            return False

        vector = self.vectors[vector_id]
        normalized_coords = np.array(new_coordinates) / np.linalg.norm(new_coordinates)
        vector.add_layer("Coordinates", normalized_coords)
        vector.add_layer("State", {**new_state, "timestamp": time.time()})
        logger.info(f"Vector {vector_id} updated to new state.")
        return True

    def secure_layer_data(self, vector_id: str) -> Optional[np.ndarray]:
        """Apply gauge transformation for secure access."""
        vector = self.get_vector(vector_id)
        if vector:
            data_vector = vector.get_layer("Coordinates")
            return self.gauge_transformation.apply_transformation(data_vector)
        return None

    def recover_layer_data(self, transformed_vector: np.ndarray) -> np.ndarray:
        """Recover original data after gauge transformation."""
        return self.gauge_transformation.reverse_transformation(transformed_vector)

    def project_data(self, vector_id: str) -> Optional[np.ndarray]:
        """Project vector data to lower dimension."""
        vector = self.get_vector(vector_id)
        if vector:
            data_vector = vector.get_layer("Coordinates")
            return self.projection.project(data_vector, self.target_dim)
        return None

    def calculate_entropy(self, vector_id: str) -> float:
        """Calculate entanglement entropy for inter-layer correlation with regularization."""
        vector = self.get_vector(vector_id)
        if vector:
            data_vector = vector.get_layer("Coordinates")
            density_matrix = np.outer(data_vector, data_vector)

            # Regularize the density matrix to prevent singularities
            epsilon = 1e-3
            regularized_density_matrix = density_matrix + np.eye(density_matrix.shape[0]) * epsilon

            # Calculate entropy
            entropy = self.entanglement_entropy.calculate_entropy(regularized_density_matrix)

            # Return only the real part to avoid complex warnings
            return entropy.real
        return 0.0

    def holographic_entropy(self) -> float:
        """Calculate holographic entropy for resilience and redundancy."""
        return self.holographic_screen.holographic_entropy()

    def secure_and_verify_consensus(self, vector_id: str) -> Tuple[Optional[np.ndarray], bool]:
        """Secure consensus data with transformation and verify."""
        vector = self.get_vector(vector_id)
        if vector:
            data_vector = vector.get_layer("Coordinates")

            # Pad data_vector to match the dimension of the transformation matrix if needed
            if data_vector.shape[0] < self.dimension:
                data_vector = np.pad(data_vector, (0, self.dimension - data_vector.shape[0]))

            secured_data = self.secure_consensus.secure_data(data_vector)

            # Pad original_vector to match the secured_data if needed
            original_vector = data_vector
            if original_vector.shape[0] < secured_data.shape[0]:
                original_vector = np.pad(original_vector, (0, secured_data.shape[0] - original_vector.shape[0]))

            is_valid = self.secure_consensus.verify_data(secured_data, original_vector)
            return secured_data, is_valid
        return None, False

    def get_vector(self, vector_id: str) -> Optional[TransactionVector]:
        return self.vectors.get(vector_id)
