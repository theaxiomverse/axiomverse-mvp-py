from abc import ABC, abstractmethod
from typing import Dict

class TrustManagerInterface(ABC):
    @abstractmethod
    def calculate_trust_score(self, node_data: Dict) -> float:
        """Calculate the trust score for a node."""
        pass

    @abstractmethod
    def ban_node(self, node_id: str) -> None:
        """Ban a node from the network."""
        pass

    @abstractmethod
    def update_trust_score(self, node_id: str, node_data: Dict) -> None:
        """Update the trust score of a node."""
        pass

    @abstractmethod
    def get_trust_score(self, node_id: str) -> float:
        """Retrieve the trust score for a specific node."""
        pass
