import blake3
from .hashing_interface import HashingInterface

class Blake3Hashing(HashingInterface):
    def hash(self, data: bytes, context: str) -> str:
        """Generate a BLAKE3 hash using a specific context."""
        hasher = blake3.blake3(context.encode())  # Use the key derivation mode with context
        hasher.update(data)
        return hasher.hexdigest()

    def verify(self, data: bytes, context: str, hash_value: str) -> bool:
        """Verify that the generated hash matches the provided hash value."""
        expected_hash = self.hash(data, context)
        return expected_hash == hash_value

    def derive_key(self, key_material: bytes, context: str) -> bytes:
        """Derive a new key using the key derivation mode with a unique context."""
        derived_key = blake3.blake3(key_material, derive_key_context=context).digest()
        return derived_key

    def extended_output(self, data: bytes, length: int) -> bytes:
        """Generate extended output of the given length."""
        return blake3.blake3(data).digest(length=length)

    def hash_file(self, file_path: str) -> str:
        """Hash a large input file using multiple threads and memory mapping."""
        file_hasher = blake3.blake3(max_threads=blake3.blake3.AUTO)
        file_hasher.update_mmap(file_path)
        return file_hasher.hexdigest()
