import base64
import json
from abc import ABC, abstractmethod
from typing import Dict
from src.modules.contract_module.contract_interface import ContractInterface, ContractTypeAlias
from kyber import Kyber512
from src.modules.crypto_module.hashing_interface import HashingInterface
from src.modules.crypto_module.blake3_hashing import Blake3Hashing
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class NFTContract:
    pass


class MediaContract:
    pass


class SensitiveDataContract:
    pass


class OracleContract:
    pass


class ContractManager:
    def __init__(self):
        self.contracts = {}
        self.hashing_interface = Blake3Hashing()  # Hashing interface for generating contract hashes

    def create_contract(self, contract_type: ContractTypeAlias, **kwargs) -> ContractInterface:
        """Create a new contract instance of the given type."""
        # Depending on the type, instantiate the appropriate contract subclass.
        if contract_type == ContractTypeAlias.TOKEN:
            contract = TokenContract(**kwargs)
        elif contract_type == ContractTypeAlias.NFT:
            contract = NFTContract(**kwargs)
        elif contract_type == ContractTypeAlias.MEDIA:
            contract = MediaContract(**kwargs)
        elif contract_type == ContractTypeAlias.SENSITIVE_DATA:
            contract = SensitiveDataContract(**kwargs)
        elif contract_type == ContractTypeAlias.ORACLE:
            contract = OracleContract(**kwargs)
        else:
            raise ValueError(f"Unknown contract type: {contract_type}")

        # Generate and assign the contract signature using Kyber 512
        contract_signature = self.generate_contract_signature(contract)
        contract.signature = contract_signature

        # Store the contract in the manager's dictionary
        self.contracts[contract.signature] = contract
        logger.info(f"Contract created with type {contract_type} and signature {contract_signature}")

        return contract

    def generate_contract_signature(self, contract: ContractInterface) -> str:
        """Generate a Kyber signature for the contract."""
        kyber = Kyber512()
        pk, sk = kyber.keygen()  # Generate the public and private key for the contract

        # Serialize contract data for signing
        contract_data = json.dumps(contract.data, sort_keys=True).encode()
        contract_hash = self.hashing_interface.hash_data(contract_data)

        # Encrypt and sign contract data using Kyber
        signature, _ = kyber.encaps(pk)

        # Combine the hash and signature for storage
        encrypted_signature = self.encrypt_signature(signature, contract_hash)
        return encrypted_signature

    def validate_contract(self, contract_signature: str) -> bool:
        """Validate a contract using its signature."""
        if contract_signature not in self.contracts:
            raise ValueError("Invalid contract signature.")

        contract = self.contracts[contract_signature]
        kyber = Kyber512()
        pk, sk = kyber.keygen()  # Generate keys for validation (would be stored securely in practice)

        # Hash contract data and verify signature
        contract_data = json.dumps(contract.data, sort_keys=True).encode()
        contract_hash = self.hashing_interface.hash_data(contract_data)
        signed_data, _ = kyber.encaps(pk)

        return signed_data == contract.signature

    def encrypt_signature(self, signature: bytes, contract_hash: bytes) -> str:
        """Encrypt the contract signature along with the contract hash."""
        # Generate random key for encryption
        encryption_key = os.urandom(32)
        iv = os.urandom(16)

        backend = default_backend()
        cipher = Cipher(algorithms.AES(encryption_key), modes.CFB(iv), backend=backend)
        encryptor = cipher.encryptor()
        encrypted_signature = encryptor.update(signature + contract_hash) + encryptor.finalize()

        # Encode the encrypted signature to base64 for storage
        return base64.b64encode(encrypted_signature).decode()


# Example contract subclass implementations
class TokenContract(ContractInterface):
    def __init__(self, name, symbol, supply_cap):
        super().__init__(ContractTypeAlias.TOKEN, name=name, symbol=symbol, supply_cap=supply_cap)
        self.name = name
        self.symbol = symbol
        self.supply_cap = supply_cap

    def execute(self, action, *args, **kwargs):
        if action == "mint":
            amount = kwargs.get('amount', 0)
            logger.info(f"Minting {amount} tokens of {self.symbol}")
        elif action == "transfer":
            recipient = kwargs.get('recipient')
            amount = kwargs.get('amount', 0)
            logger.info(f"Transferring {amount} tokens to {recipient}")

    def validate(self):
        if not self.name or not self.symbol or self.supply_cap <= 0:
            raise ValueError("Invalid TokenContract fields.")

# Additional contract types like NFTContract, MediaContract, etc.
# Implement similar to TokenContract with relevant methods.
