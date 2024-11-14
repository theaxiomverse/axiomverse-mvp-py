from .interfaces.vector_interface import VectorInterface
from .transaction_layer import TransactionLayer
import numpy as np
import pickle

class TransactionVector(VectorInterface):
    def __init__(self):
        """Initialize an empty transactional vector with multiple layers."""
        self.layers = {}  # Store layers by name or type

    def add_layer(self, layer_name: str, data):
        """Add a new layer to the vector with data serialization based on type."""
        # Handle numpy array data (e.g., coordinate data)
        if isinstance(data, np.ndarray):
            byte_data = data.tobytes()
        # Handle dictionary data (e.g., state information) using pickle
        elif isinstance(data, dict):
            byte_data = pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported data type for layer: {type(data)}")

        self.layers[layer_name] = TransactionLayer(byte_data)
        print(f"Layer '{layer_name}' added with serialized data.")

    def get_layer(self, layer_name: str):
        """Retrieve and deserialize a specific layer by name."""
        layer = self.layers.get(layer_name)
        if layer is None:
            return None

        # Deserialize based on stored type
        byte_data = layer.get_data()
        try:
            return np.frombuffer(byte_data)  # Attempt to load as numpy array
        except ValueError:
            return pickle.loads(byte_data)   # If not, load as dictionary

    def get_all_layers(self):
        """Retrieve all layers in the vector."""
        return {name: self.get_layer(name) for name in self.layers}
