# Step 1: Define Crypto Interface - crypto_interface.py
from abc import ABC, abstractmethod

class CryptoInterface(ABC):
    @abstractmethod
    def generate_keys(self):
        pass

    @abstractmethod
    def sign_data(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        pass

class KeyInterface(ABC):
    @abstractmethod
    def encrypt(self, data: bytes, public_key: bytes) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, encrypted_data: bytes, private_key: bytes) -> bytes:
        pass

    @abstractmethod
    def sign(self, data: bytes, private_key: bytes) -> bytes:
        pass

    @abstractmethod
    def get_public_key(self, private_key: bytes) -> bytes:
        pass

    @abstractmethod
    def derive_key(self, password: str, salt: bytes) -> bytes:
        pass
