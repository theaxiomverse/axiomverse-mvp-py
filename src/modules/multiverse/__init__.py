# modules/multiverse/__init__.py
from .consensus.secure_consensus_layer import SecureConsensusLayer
from .entanglement import EntanglementManager
from .holography import HolographyManager
from .projection import ProjectionManager
from .security import SecurityManager

__all__ = [
    'SecureConsensusLayer',
    'EntanglementManager',
    'HolographyManager',
    'ProjectionManager',
    'SecurityManager'
]


class ConsensusManager:
    pass