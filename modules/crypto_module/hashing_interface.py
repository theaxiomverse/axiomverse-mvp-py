from abc import ABC, abstractmethod

class HashingInterface(ABC):
    @abstractmethod
    def hash(self, data: bytes, context: str) -> str:
        """Generate a hash for given data and context."""
        pass

    @abstractmethod
    def verify(self, data: bytes, context: str, hash_value: str) -> bool:
        """Verify the hash of given data and context matches the expected hash value."""
        pass
