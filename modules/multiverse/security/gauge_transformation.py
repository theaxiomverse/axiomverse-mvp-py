import numpy as np
from scipy.linalg import expm
from .gauge_transformation_interface import GaugeTransformationInterface

class GaugeTransformation(GaugeTransformationInterface):
    def __init__(self, dimension):
        self.dimension = dimension
        self.connection = np.random.randn(dimension, dimension)  # Random gauge field

    def apply_transformation(self, data_vector: np.ndarray) -> np.ndarray:
        # Generate a square matrix that matches the dimension of the input vector
        U = np.eye(data_vector.shape[0])  # Identity matrix of size matching data_vector
        return np.dot(U, data_vector)

    def reverse_transformation(self, transformed_vector: np.ndarray) -> np.ndarray:
        U_inv = np.linalg.inv(expm(self.connection))  # Inverse transformation
        return np.dot(U_inv, transformed_vector)
