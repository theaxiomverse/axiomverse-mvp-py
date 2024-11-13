import numpy as np
from .projection_interface import ProjectionInterface

class DimensionalProjection(ProjectionInterface):
    def __init__(self, dimension):
        self.dimension = dimension

    def project(self, vector: np.ndarray, target_dim: int) -> np.ndarray:
        if target_dim > self.dimension:
            raise ValueError("Target dimension cannot exceed original dimension.")
        return vector[:target_dim]
