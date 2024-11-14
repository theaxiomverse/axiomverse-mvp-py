# vector_module/transaction_protocol.py

import hashlib
import time
import logging
from typing import List, Optional
from vector_module.quantum_vector_manager import QuantumVectorManager
from vector_module.transaction_matrix import TransactionMatrix

logger = logging.getLogger(__name__)

class TransactionProtocol:
    def __init__(self, vector_manager: QuantumVectorManager, transaction_matrix: TransactionMatrix):
        # Initialize with a reference to QuantumVectorManager and TransactionMatrix
        self.vector_manager = vector_manager
        self.transaction_matrix = transaction_matrix
        # List to store pending transactions
        self.pending_transactions = []
        # Set to store processed transaction IDs (for double-spend prevention)
        self.processed_transactions = set()
        # Dictionary to track locked vectors
        self.locked_vectors = set()
        logger.info("TransactionProtocol initialized")

    def create_transaction(self, tx_type: str, sender: str, vector_data: Optional[List[float]] = None, **kwargs):
        # Generate a unique transaction ID
        tx_id = hashlib.sha256(f"{sender}{time.time()}".encode()).hexdigest()
        signature = hashlib.sha256(f"{tx_id}{sender}".encode()).hexdigest()

        # Check if a transaction with this ID or affecting the same vector has already been processed
        if tx_id in self.processed_transactions:
            logger.warning(f"Double-spend attempt detected: Transaction {tx_id} already processed.")
            return {"error": "Double-spend attempt detected: Transaction already processed."}

        # Add the transaction to pending_transactions for processing
        transaction = {
            "tx_id": tx_id,
            "tx_type": tx_type,
            "sender": sender,
            "vector_data": vector_data,
            "signature": signature,
            "timestamp": time.time(),
            **kwargs
        }
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction {tx_id} of type {tx_type} created.")
        return transaction

    def process_transactions(self):
        # Process each pending transaction
        for transaction in self.pending_transactions:
            tx_id = transaction["tx_id"]
            tx_type = transaction["tx_type"]
            vector_id = transaction.get("vector_id")

            # Check if the vector is locked
            if vector_id in self.locked_vectors:
                logger.warning(f"Transaction {tx_id} cannot be processed: Vector {vector_id} is currently locked.")
                continue

            # Lock the vector to prevent concurrent modification
            self.locked_vectors.add(vector_id)

            try:
                if tx_type == "VECTOR_CREATE" and transaction["vector_data"]:
                    # Create a new vector
                    self.vector_manager.create_vector(vector_id=tx_id, coordinates=transaction["vector_data"])
                    self.transaction_matrix.add_transaction("Time", "Create", vector_id=tx_id, data=transaction)

                elif tx_type == "VECTOR_UPDATE" and transaction["vector_data"]:
                    # Update an existing vector
                    new_state = {"state": "UPDATED"}
                    self.vector_manager.update_vector(vector_id=tx_id, new_coordinates=transaction["vector_data"], new_state=new_state)

                # Mark transaction as processed
                self.processed_transactions.add(tx_id)

            except Exception as e:
                logger.error(f"Error processing transaction {tx_id}: {e}")
            finally:
                # Unlock the vector
                self.locked_vectors.remove(vector_id)

        # Clear pending transactions
        self.pending_transactions.clear()
