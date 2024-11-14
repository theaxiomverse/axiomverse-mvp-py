from abc import ABC, abstractmethod
from typing import Dict, Any

class TransactionManagerInterface(ABC):
    @abstractmethod
    def create_transaction(self, tx_id: str, tx_data: Dict[str, Any]) -> None:
        """Create a new transaction with the given ID and data."""
        pass

    @abstractmethod
    def confirm_transaction(self, tx_id: str) -> None:
        """Confirm a transaction."""
        pass

    @abstractmethod
    def retrieve_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Retrieve transaction details using the transaction ID."""
        pass

    @abstractmethod
    def delete_transaction(self, tx_id: str) -> None:
        """Delete a transaction."""
        pass
