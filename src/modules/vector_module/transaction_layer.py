# /transaction_layer.py

from .interfaces.layer_interface import LayerInterface

class TransactionLayer(LayerInterface):
    def __init__(self, data):
        """Initialize a layer with specific transaction data."""
        self.data = data

    def get_data(self):
        """Retrieve data for this layer."""
        return self.data
