import numpy as np

class MultiverseBasis:
    def __init__(self, dimension):
        """Initialize an orthonormal basis for the Multiverse Vector Space."""
        self.dimension = dimension
        self.basis_vectors = [self.create_basis_vector(i) for i in range(dimension)]

    def create_basis_vector(self, index):
        """Generate a basis vector with 1 at 'index' and 0 elsewhere."""
        vector = np.zeros(self.dimension)
        vector[index] = 1
        return vector

    def get_basis(self):
        """Return the set of basis vectors."""
        return self.basis_vectors
