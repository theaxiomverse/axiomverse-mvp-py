import numpy as np
from scipy.linalg import expm

class GaugeField:
    def __init__(self, dimension):
        """Initialize the gauge field with a given Lie algebra dimension."""
        self.dimension = dimension
        self.connection = np.random.randn(dimension, dimension)  # Random initial connection

    def gauge_transform(self, vector, U):
        """Apply a gauge transformation to the vector."""
        return U @ vector

    def update_connection(self, gauge_potential):
        """Update the connection based on a new gauge potential (gauge field strength)."""
        self.connection += gauge_potential


class GaugeConnection(GaugeField):
    def __init__(self, dimension):
        super().__init__(dimension)

    def connection_operator(self, vector):
        """Apply the connection operator to a vector in MVS."""
        # Ensure `vector` is a NumPy array and compatible for multiplication
        vector = np.array(vector)
        return np.dot(self.connection, vector)  # Use np.dot for compatibility

    def gauge_transformation(self, vector, U):
        """Transform the vector under the gauge field U."""
        # Ensure `U` and `vector` are NumPy arrays
        U = np.array(U)
        vector = np.array(vector)

        # Perform matrix multiplication explicitly
        transformed_vector = np.dot(expm(U), vector)
        return transformed_vector