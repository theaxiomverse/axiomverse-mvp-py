# vector_module/interfaces/vector_interface.py

from abc import ABC, abstractmethod
from .layer_interface import LayerInterface

class VectorInterface(ABC):
    @abstractmethod
    def add_layer(self, layer_name: str, data):
        """Add a new layer to the vector."""
        pass

    @abstractmethod
    def get_layer(self, layer_name: str) -> LayerInterface:
        """Retrieve a specific layer by name."""
        pass

    @abstractmethod
    def get_all_layers(self):
        """Retrieve all layers in the vector."""
        pass
