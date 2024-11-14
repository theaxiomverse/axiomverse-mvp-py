# vector_module/interfaces/matrix_interface.py

from abc import ABC, abstractmethod
from .vector_interface import VectorInterface

class MatrixInterface(ABC):
    @abstractmethod
    def add_transaction(self, row_key, col_key, layer_name, data):
        """Add transaction data to a specific vector in the matrix."""
        pass

    @abstractmethod
    def get_transaction_vector(self, row_key, col_key) -> VectorInterface:
        """Retrieve the transaction vector at a specific matrix cell."""
        pass

    @abstractmethod
    def query_layer(self, row_key, col_key, layer_name):
        """Query a specific layer in a specific transaction vector."""
        pass
