from src.modules.trust_module.trust_manager_interface import TrustManagerInterface
from typing import Dict
import math
import logging

logger = logging.getLogger(__name__)

class TrustManager(TrustManagerInterface):
    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor
        self.node_trust_scores = {}

    def calculate_trust_score(self, node_data: Dict) -> float:
        """Calculate the trust score for a node based on the given data."""
        uptime = node_data.get("uptime", 0.0)
        latency = node_data.get("latency", 1.0)
        age = node_data.get("age", 0.0)
        peer_recognition = node_data.get("peer_recognition", 0.0)
        stability = node_data.get("stability", 0.0)

        inflated_age_score = min(1.0, age * 0.1 * math.pow(1.021416, age))
        trust_score = (
            0.2 * uptime +
            0.2 * (1 - latency) +
            0.2 * inflated_age_score +
            0.2 * peer_recognition +
            0.2 * stability
        )

        logger.debug(f"Calculated trust score: {trust_score} for node: {node_data.get('id')}")
        return trust_score

    def ban_node(self, node_id: str) -> None:
        """Ban a node from the network by setting its trust score to a negative value."""
        if node_id in self.node_trust_scores:
            self.node_trust_scores[node_id] = -1.0
            logger.info(f"Node {node_id} has been banned.")
        else:
            logger.warning(f"Attempted to ban unknown node: {node_id}")

    def update_trust_score(self, node_id: str, node_data: Dict) -> None:
        """Update the trust score of a node."""
        trust_score = self.calculate_trust_score(node_data)
        self.node_trust_scores[node_id] = trust_score

        # Ban node if trust score is negative
        if trust_score < 0:
            self.ban_node(node_id)

        logger.info(f"Updated trust score for node {node_id}: {trust_score}")

    def get_trust_score(self, node_id: str) -> float:
        """Retrieve the trust score for a specific node."""
        return self.node_trust_scores.get(node_id, 0.0)
