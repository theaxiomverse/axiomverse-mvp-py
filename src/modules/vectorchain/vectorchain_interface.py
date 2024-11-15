from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

from src.modules.transaction_module import TransactionManagerInterface
from src.modules.vectorchain import logger


class VectorChainInterface(ABC):
    @abstractmethod
    async def submit_transaction(self, transaction: Dict) -> str:
        """Submit transaction to chain."""
        pass

    @abstractmethod
    async def process_transactions(self) -> None:
        """Process pending transactions."""
        pass

    @abstractmethod
    async def get_transaction_status(self, tx_id: str) -> Dict:
        """Get status of transaction."""
        pass


class VectorManagerInterface(ABC):
    @abstractmethod
    async def create_vector(self, vector_id: str, coordinates: List[float]) -> str:
        """Create new vector."""
        pass

    @abstractmethod
    async def get_vector(self, vector_id: str) -> Optional[np.ndarray]:
        """Retrieve vector by ID."""
        pass

    @abstractmethod
    async def update_vector(self, vector_id: str, new_coordinates: List[float]) -> bool:
        """Update existing vector."""
        pass


class ZKPSystemInterface(ABC):
    @abstractmethod
    async def prove_vector_knowledge(self, coordinates: np.ndarray, identifier: str) -> tuple:
        """Generate ZKP proof."""
        pass

    @abstractmethod
    async def verify_proof(self, commitment: bytes, proof: Dict, identifier: str) -> bool:
        """Verify ZKP proof."""
        pass


class VectorChainProcessor(VectorChainInterface):
    def __init__(self,
                 vector_manager: VectorManagerInterface,
                 transaction_manager: TransactionManagerInterface,
                 zkp_system: ZKPSystemInterface):
        self.vector_manager = vector_manager
        self.transaction_manager = transaction_manager
        self.zkp = zkp_system
        self.pending_transactions: List[Dict] = []
        self.processed_vectors: Dict[str, np.ndarray] = {}

    async def submit_transaction(self, transaction: Dict) -> str:
        if not self._validate_transaction_structure(transaction):
            raise ValueError("Invalid transaction structure")

        vector_id = f"tx_{transaction['tx_id']}"
        coordinates = self._extract_transaction_coordinates(transaction)

        await self.vector_manager.create_vector(vector_id, coordinates)
        commitment, proof = await self.zkp.prove_vector_knowledge(coordinates, vector_id)

        enriched_transaction = {
            **transaction,
            'vector_id': vector_id,
            'proof': proof,
            'commitment': commitment,
            'timestamp': datetime.now().timestamp()
        }

        self.pending_transactions.append(enriched_transaction)
        return vector_id

    async def process_transactions(self) -> None:
        if not self.pending_transactions:
            return

        batch = self.pending_transactions[:100]
        valid_transactions = []

        for tx in batch:
            if await self._validate_and_process_transaction(tx):
                valid_transactions.append(tx)

        for tx in valid_transactions:
            self.processed_vectors[tx['vector_id']] = await self.vector_manager.get_vector(tx['vector_id'])

        self.pending_transactions = [tx for tx in self.pending_transactions if tx not in valid_transactions]

    async def get_transaction_status(self, tx_id: str) -> Dict:
        vector_id = f"tx_{tx_id}"
        if vector_id in self.processed_vectors:
            return {"status": "processed", "vector_id": vector_id}

        for tx in self.pending_transactions:
            if tx['tx_id'] == tx_id:
                return {"status": "pending", "vector_id": vector_id}

        return {"status": "not_found", "vector_id": vector_id}

    async def _validate_and_process_transaction(self, transaction: Dict) -> bool:
        try:
            vector_id = transaction['vector_id']

            if not await self.zkp.verify_proof(
                    transaction['commitment'],
                    transaction['proof'],
                    vector_id
            ):
                return False

            vector = await self.vector_manager.get_vector(vector_id)
            if not vector:
                return False

            result = await self.transaction_manager.process_transaction(transaction)
            return bool(result)

        except Exception as e:
            logger.error(f"Transaction processing error: {e}")
            return False

    def _extract_transaction_coordinates(self, transaction: Dict) -> np.ndarray:
        coordinates = []

        numerical_fields = ['amount', 'timestamp', 'fee']
        for field in numerical_fields:
            if field in transaction:
                coordinates.append(float(transaction[field]))

        if 'metadata' in transaction and isinstance(transaction['metadata'], dict):
            coordinates.extend([
                float(value) for value in transaction['metadata'].values()
                if isinstance(value, (int, float))
            ])

        while len(coordinates) < self.vector_manager.dimensions:
            coordinates.append(0.0)

        return np.array(coordinates)

    def _validate_transaction_structure(self, transaction: Dict) -> bool:
        required_fields = {'tx_id', 'sender', 'receiver', 'amount'}
        return all(field in transaction for field in required_fields)