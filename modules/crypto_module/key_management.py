import os
from typing import Tuple
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from oqs import Signature,  KeyEncapsulation
import base64

class KeyManagement:
    def __init__(self):
        self.key = os.urandom(32)  # Using a 256-bit key for AES encryption

        self.kyber = KeyEncapsulation('Kyber512')

    def generate_keypair(self) -> Tuple[str, str]:
        """Generate a keypair using Kyber-512."""
        pk = self.kyber.generate_keypair()
        sk = self.kyber.export_secret_key()
        return base64.b64encode(pk).decode(), base64.b64encode(sk).decode()

    def encapsulate(self, public_key: str) -> Tuple[str, str]:
        """Encapsulate a symmetric key using the provided public key."""
        pk = base64.b64decode(public_key.encode())
        key, ciphertext = self.kyber.encaps(pk)
        return base64.b64encode(key).decode(), base64.b64encode(ciphertext).decode()

    def decapsulate(self, secret_key: str, ciphertext: str) -> str:
        """Decapsulate a ciphertext using the provided secret key."""
        sk = base64.b64decode(secret_key.encode())
        ct = base64.b64decode(ciphertext.encode())
        key = self.kyber.decap_secret(ct)
        return base64.b64encode(key).decode()

    def encrypt(self, plaintext: bytes) -> bytes:
        # Create a random IV for AES-CBC
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the plaintext to be a multiple of block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        # Encrypt the padded data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Prepend the IV to the ciphertext
        encrypted_data = iv + ciphertext

        # Return the base64 encoded version of the encrypted data
        return encrypted_data

    def decrypt(self, encrypted_data):
        # Decode the base64 encoded data
        encrypted_data_bytes = base64.urlsafe_b64decode(encrypted_data)

        # Extract the IV from the beginning of the encrypted data
        iv = encrypted_data_bytes[:16]
        ciphertext = encrypted_data_bytes[16:]

        # Create a cipher object with the extracted IV
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the ciphertext
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        # Return the decrypted plaintext as a string
        return plaintext.decode('utf-8')

# Example usage:
# key_mgmt = KeyManagement()
# pk, sk = key_mgmt.generate_keypair()
# key, ct = key_mgmt.encapsulate(pk)
# derived_key = key_mgmt.decapsulate(sk, ct)
