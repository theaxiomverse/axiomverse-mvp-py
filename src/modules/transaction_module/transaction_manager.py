import asyncio
import json
import logging
import pickle
from typing import Dict, Tuple

import numpy as np
from aioipfs import AsyncIPFS
from ..zkp.qzkp_optimized import QuantumZKP
from ..events_module.event_emitter import EventEmitter
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from oqs import Signature, KeyEncapsulation  # Import Falcon from oqs-python
from ..crypto_module.blake3_hashing import Blake3Hashing  # Import Blake3Hashing for hashing
import os

logger = logging.getLogger(__name__)


class TransactionManager:
    def __init__(self, dimensions: int = 8, security_level: int = 128):
        self.ipfs_client = AsyncIPFS()  # Instantiate AsyncIPFS client
        self.event_emitter = EventEmitter()  # Instantiate EventEmitter
        self.zkp = QuantumZKP(dimensions, security_level)
        self.kyber = KeyEncapsulation('Kyber512')# Initialize Kyber512 for key exchange
        self.hasher = Blake3Hashing()  # Initialize Blake3Hashing for hashing needs
        logger.info("TransactionManager initialized with IPFS and encrypted storage using Kyber key exchange.")

    def _encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data with AES-GCM for confidentiality and integrity."""
        iv = os.urandom(12)  # AES-GCM requires a 12-byte IV
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        return iv + encryptor.tag + encrypted_data  # Concatenate IV, tag, and encrypted data

    def _decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data with AES-GCM."""
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        cipher_text = encrypted_data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(cipher_text) + decryptor.finalize()

    def _derive_shared_key(self, user_private_key: bytes, recipient_public_key: bytes) -> Tuple[bytes, bytes, bytes]:
        """Derive a shared encryption key using Kyber key encapsulation."""
        try:
            user_public_key, ephemeral_private_key = self.kyber.generate_keypair()
            shared_key, ciphertext = self.kyber.encapsulate(recipient_public_key)
            return shared_key, ciphertext, user_public_key
        except Exception as e:
            logger.error(f"Failed to derive shared key with Kyber: {e}")
            raise ValueError("Shared key derivation failed.")

    async def create_transaction(self, transaction_data: Dict, user_private_key: bytes, recipient_public_key: bytes) -> Tuple[str, str]:
        """Store a transaction on IPFS, encrypt it using Kyber-derived shared key, and return the CID and metadata CID."""
        transaction_id = self._generate_transaction_id(transaction_data)
        latent_vector_layer = self._create_latent_vector_layer(transaction_data)

        commitment, proof = self.zkp.prove_vector_knowledge(latent_vector_layer, transaction_id)
        transaction_data["commitment"] = pickle.dumps(commitment).hex()
        transaction_data["proof"] = pickle.dumps(proof).hex()
        transaction_data["confirmed"] = False

        # Convert transaction data to JSON
        plaintext_data = json.dumps(transaction_data).encode('utf-8')

        # Derive shared encryption key using Kyber key exchange
        shared_key, ciphertext, user_public_key = self._derive_shared_key(user_private_key, recipient_public_key)

        # Encrypt transaction data with shared key
        encrypted_data = self._encrypt_data(plaintext_data, shared_key)

        # Store encrypted transaction data on IPFS
        cid = await self.ipfs_client.add_bytes(encrypted_data)

        # Prepare and encrypt metadata
        metadata = {
            "user_public_key": user_public_key.hex(),
            "ciphertext": ciphertext.hex()
        }
        metadata_plaintext = json.dumps(metadata).encode('utf-8')
        encrypted_metadata = self._encrypt_data(metadata_plaintext, shared_key)
        metadata_cid = await self.ipfs_client.add_bytes(encrypted_metadata)

        # Emit event for stored transaction
        await self.event_emitter.emit_event("transaction_stored", {"transaction_id": cid, "metadata_cid": metadata_cid})
        logger.info(f"Transaction {transaction_id} stored on IPFS with CID {cid}.")

        return cid, metadata_cid

    async def retrieve_transaction_metadata(self, metadata_cid: str, shared_key: bytes) -> Dict:
        """Retrieve and decrypt transaction metadata from IPFS using metadata CID and shared key."""
        try:
            encrypted_metadata = await self.ipfs_client.cat(metadata_cid)
            metadata_plaintext = self._decrypt_data(encrypted_metadata, shared_key)
            metadata = json.loads(metadata_plaintext.decode('utf-8'))
            logger.info(f"Retrieved transaction metadata from IPFS with CID {metadata_cid}.")
            return metadata
        except Exception as e:
            logger.error(f"Failed to retrieve or decrypt transaction metadata with CID {metadata_cid}: {e}")
            raise ValueError("Transaction metadata retrieval failed.")

    async def confirm_transaction(self, transaction_id: str, metadata_cid: str, recipient_private_key: bytes) -> None:
        """Confirm the transaction by updating its status on IPFS and move it to the transaction layer."""
        # Retrieve encrypted transaction data from IPFS
        encrypted_data = await self.ipfs_client.cat(transaction_id)

        # Retrieve transaction metadata and derive shared key using recipient's private key
        transaction_metadata = await self.retrieve_transaction_metadata(metadata_cid, recipient_private_key)
        ciphertext = bytes.fromhex(transaction_metadata["ciphertext"])
        shared_key = self.kyber.decapsulate(ciphertext, recipient_private_key)

        # Decrypt transaction data
        plaintext_data = self._decrypt_data(encrypted_data, shared_key)
        transaction_data = json.loads(plaintext_data.decode('utf-8'))

        commitment = pickle.loads(bytes.fromhex(transaction_data['commitment']))
        proof = pickle.loads(bytes.fromhex(transaction_data['proof']))

        # Verify proof before confirmation
        if not self.zkp.verify_proof(commitment, proof, transaction_id):
            logger.error(f"Proof verification failed for transaction {transaction_id}.")
            raise ValueError("Proof verification failed. Transaction confirmation denied.")

        # Update the vector layer: remove from latent layer and add to transaction layer
        self._update_vector_layers(transaction_id)

        # Mark transaction as confirmed and re-encrypt the data
        transaction_data['confirmed'] = True
        new_plaintext_data = json.dumps(transaction_data).encode('utf-8')
        new_encrypted_data = self._encrypt_data(new_plaintext_data, shared_key)

        # Store the updated encrypted data on IPFS
        new_cid = await self.ipfs_client.add_bytes(new_encrypted_data)

        # Emit event for confirmed transaction
        await self.event_emitter.emit_event("transaction_confirmed", {"transaction_id": new_cid})
        logger.info(f"Transaction {transaction_id} confirmed and updated on IPFS with new CID {new_cid}.")

    def _update_vector_layers(self, transaction_id: str) -> None:
        """Move transaction from latent vector layer to transaction layer in vector storage."""
        try:
            # Example operation to represent moving a transaction ID from the latent layer to the transaction layer
            # Actual implementation of vector layer management depends on the specifics of your vector structure
            logger.info(f"Transaction {transaction_id} moved from latent layer to transaction layer.")
        except Exception as e:
            logger.error(f"Failed to update vector layers for transaction {transaction_id}: {e}")
            raise ValueError("Vector layer update failed.")

    async def retrieve_transaction(self, transaction_id: str, metadata_cid: str, recipient_private_key: bytes) -> Dict:
        """Retrieve and decrypt a stored transaction from IPFS using Kyber-derived shared key."""
        # Retrieve encrypted transaction data from IPFS
        encrypted_data = await self.ipfs_client.cat(transaction_id)

        # Retrieve transaction metadata and decrypt shared key using recipient's private key
        transaction_metadata = await self.retrieve_transaction_metadata(metadata_cid, recipient_private_key)
        ciphertext = bytes.fromhex(transaction_metadata["ciphertext"])
        shared_key = self.kyber.decapsulate(ciphertext, recipient_private_key)

        # Decrypt the data
        plaintext_data = self._decrypt_data(encrypted_data, shared_key)
        transaction_data = json.loads(plaintext_data.decode('utf-8'))

        commitment = pickle.loads(bytes.fromhex(transaction_data['commitment']))
        proof = pickle.loads(bytes.fromhex(transaction_data['proof']))

        if not transaction_data['confirmed']:
            raise ValueError("Transaction is not confirmed yet.")

        # Verify proof before returning data
        if not self.zkp.verify_proof(commitment, proof, transaction_id):
            logger.error(f"Proof verification failed for transaction {transaction_id}.")
            raise ValueError("Proof verification failed. Retrieval denied.")

        await self.event_emitter.emit_event("transaction_retrieved", {"transaction_id": transaction_id})
        logger.info(f"Transaction {transaction_id} retrieved successfully from IPFS.")

        return transaction_data

    def _generate_transaction_id(self, transaction_data: Dict) -> str:
        """Generate a unique transaction ID based on transaction data using Blake3."""
        data_bytes = json.dumps(transaction_data, sort_keys=True).encode('utf-8')
        return self.hasher.hash(data_bytes, context="transaction_id")

    def _create_latent_vector_layer(self, transaction_data: Dict) -> np.ndarray:
        """Create a latent vector layer from numerical transaction data."""
        numerical_values = [value for value in transaction_data.values() if isinstance(value, (int, float))]
        latent_vector_layer = np.array(numerical_values + [0] * (self.zkp.dimensions - len(numerical_values)))
        return latent_vector_layer

    async def close(self):
        """Close the IPFS client connection."""
        await self.ipfs_client.close()
        logger.info("IPFS client connection closed.")

    async def stop(self):
        pass

    async def start(self):
        pass
