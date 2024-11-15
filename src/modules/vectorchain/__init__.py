from dataclasses import dataclass
from typing import Optional
import logging
import time
from src.modules.account_module.account_manager import AccountManager
from src.modules.address_module.address_manager import AddressManager
from src.modules.crypto_module.blake3_hashing import Blake3Hashing
from src.modules.vector_module.quantum_vector_manager import QuantumVectorManager
from src.modules.transaction_module.transaction_manager import TransactionManager

logger = logging.getLogger(__name__)


@dataclass
class NodeIdentity:
    account_id: str
    address: str


class AxiomChain:
    def __init__(self):
        self.account_manager = AccountManager()
        self.address_manager = AddressManager()
        self.vector_manager = QuantumVectorManager()
        self.transaction_manager = TransactionManager()
        self.hasher = Blake3Hashing()
        self.identity: Optional[NodeIdentity] = None

    async def initialize_node(self, ip_address: str) -> NodeIdentity:
        """Initialize node with account and address."""
        try:
            # Generate account ID
            account_id = self._generate_account_id()

            # Create account
            await self.account_manager.create_account(account_id, ip_address)

            # Generate address for this node
            address = self.address_manager.generate_geohashed_address(ip_address, "node")

            # Store identity
            self.identity = NodeIdentity(account_id, address)
            logger.info(f"Node initialized with account {account_id} and address {address}")

            return self.identity

        except Exception as e:
            logger.error(f"Failed to initialize node: {e}")
            raise

    def _generate_account_id(self) -> str:
        """Generate unique account ID for node."""
        seed = f"node_{time.time()}"
        return self.hasher.hash(seed.encode(), "node_account")

    def get_identity(self) -> Optional[NodeIdentity]:
        """Get current node identity."""
        return self.identity

    async def start(self):
        """Start the chain with basic components and genesis."""
        try:
            logger.info("Starting AxiomChain...")

            # Initialize vector manager and transaction manager
            await self.vector_manager.start()
            await self.transaction_manager.start()

            # Create genesis if not exists
            if not self.identity:
                raise ValueError("Node must be initialized before starting chain")

            await self._create_genesis()
            logger.info("AxiomChain started successfully")
        except Exception as e:
            logger.error(f"Failed to start chain: {e}")
            raise

    async def _create_genesis(self):
        """Create genesis vector and transaction."""
        try:
            # Create genesis vector in latent layer
            genesis_coordinates = [0.0] * self.vector_manager.dimension
            genesis_vector = await self.vector_manager.create_vector(
                vector_id="genesis",
                coordinates=genesis_coordinates
            )

            # Create genesis transaction
            genesis_tx = {
                "tx_id": "genesis",
                "tx_type": "GENESIS",
                "sender": self.identity.account_id,
                "vector_id": genesis_vector.id,
                "timestamp": time.time()
            }

            # Move vector to transaction layer
            await self.vector_manager.secure_layer_data(genesis_vector.id)

            # Process genesis transaction
            await self.transaction_manager.create_transaction(genesis_tx)

            logger.info("Genesis created successfully")
            return genesis_tx

        except Exception as e:
            logger.error(f"Failed to create genesis: {e}")
            raise

    async def stop(self):
        """Stop chain components."""
        try:
            logger.info("Stopping AxiomChain...")

            # Stop managers
            await self.vector_manager.stop()
            await self.transaction_manager.stop()
            await self.account_manager.cleanup()

            logger.info("AxiomChain stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop chain: {e}")
            raise