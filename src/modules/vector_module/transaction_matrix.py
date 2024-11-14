# /transaction_matrix.py

from .interfaces.matrix_interface import MatrixInterface
from .transaction_vector import TransactionVector

class TransactionMatrix(MatrixInterface):
    def __init__(self, row_criteria, col_criteria):
        """Initialize a matrix with rows and columns organized by specific criteria."""
        self.matrix = [[TransactionVector() for _ in col_criteria] for _ in row_criteria]
        self.row_criteria = row_criteria  # E.g., time periods (months, years)
        self.col_criteria = col_criteria  # E.g., transaction types (payment, deposit, transfer)

    def add_transaction(self, row_key, col_key, layer_name, data):
        """Add transaction data to a specific vector in the matrix."""
        row = self.row_criteria.index(row_key)
        col = self.col_criteria.index(col_key)
        self.matrix[row][col].add_layer(layer_name, data)
        print(f"Transaction added to ({row_key}, {col_key}) in layer '{layer_name}'.")

    def get_transaction_vector(self, row_key, col_key) -> TransactionVector:
        """Retrieve the transaction vector at a specific matrix cell."""
        row = self.row_criteria.index(row_key)
        col = self.col_criteria.index(col_key)
        return self.matrix[row][col]

    def query_layer(self, row_key, col_key, layer_name):
        """Query a specific layer in a specific transaction vector."""
        vector = self.get_transaction_vector(row_key, col_key)
        layer = vector.get_layer(layer_name)
        if layer:
            return layer.get_data()
        else:
            return None
