import numpy as np


class MultiverseMetric:
    def __init__(self, dimension):
        """Initialize the metric tensor for the MVS with a given dimension."""
        self.dimension = dimension
        self.metric_tensor = np.eye(dimension)  # Simple Euclidean metric; extend as needed

    def compute_metric(self, vector1, vector2):
        """Compute distance between two vectors using the metric tensor."""
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        return np.sqrt((v1 - v2).T @ self.metric_tensor @ (v1 - v2))
