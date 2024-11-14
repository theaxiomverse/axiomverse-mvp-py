# vector_module/interfaces/layer_interface.py

from abc import ABC, abstractmethod

class LayerInterface(ABC):
    @abstractmethod
    def get_data(self):
        """Retrieve data for this layer."""
        pass
