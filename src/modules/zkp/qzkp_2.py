import json
import numpy as np
import hashlib
import logging
import time
from typing import Tuple, List, Dict
from oqs import Signature
from joblib import Parallel, delayed
from numba import njit

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@njit
def adjust_to_square_length(vector: np.ndarray) -> np.ndarray:
    target_length = int(np.ceil(np.sqrt(len(vector))) ** 2)
    if len(vector) < target_length:
        padded_vector = np.zeros(target_length, dtype=vector.dtype)
        padded_vector[:len(vector)] = vector
        return padded_vector
    return vector

@njit
def calculate_entropy(amplitudes: np.ndarray) -> float:
    probabilities = np.abs(amplitudes) ** 2
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    return entropy

def generate_measurements(state_coordinates: np.ndarray, security_level: int) -> List[Tuple[int, float, float]]:
    num_measurements = security_level // 8
    basis_indices = np.random.randint(0, len(state_coordinates), size=num_measurements)
    amplitudes = state_coordinates[basis_indices]
    probabilities = np.abs(amplitudes) ** 2
    phases = np.angle(amplitudes)

    # Return measurements as tuples for efficiency
    return [(int(idx), float(prob), float(phase)) for idx, prob, phase in zip(basis_indices, probabilities, phases)]

def generate_commitment(coordinates: np.ndarray, coherence: float, identifier: str) -> bytes:
    h = hashlib.sha3_256()
    h.update(coordinates.tobytes())
    h.update(str(coherence).encode())
    h.update(identifier.encode())
    return h.digest()

def prepare_message_for_signing(proof: dict, commitment: bytes) -> bytes:
    proof_copy = {k: v for k, v in proof.items() if k != "signature"}
    serialized_message = json.dumps(
        proof_copy, sort_keys=True, default=complex_encoder, separators=(',', ':')
    ).encode('utf-8')
    return serialized_message + commitment

def complex_encoder(obj):
    if isinstance(obj, complex):
        return {'real': obj.real, 'imag': obj.imag}
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def prove_vector_knowledge_worker(vector: np.ndarray, identifier: str, dimensions: int, security_level: int) -> Tuple[bytes, Dict]:
    vector = vector / np.linalg.norm(vector)
    vector = adjust_to_square_length(vector)

    phase = np.zeros(len(vector))
    coordinates = vector * np.exp(1j * phase)
    coherence = np.mean(np.abs(coordinates))
    entropy = calculate_entropy(coordinates)

    commitment = generate_commitment(coordinates, coherence, identifier)
    measurements = generate_measurements(coordinates, security_level)

    proof = {
        'quantum_dimensions': dimensions,
        'basis_coefficients': [complex(c) for c in coordinates],
        'measurements': measurements,
        'state_metadata': {
            'coherence': coherence,
            'entanglement': entropy,
            'identifier': identifier
        },
        'identifier': identifier
    }
    message = prepare_message_for_signing(proof, commitment)

    falcon_signature = Signature("Falcon-512")
    falcon_signature.generate_keypair()
    signature = falcon_signature.sign(message)
    proof['signature'] = signature.hex()

    return commitment, proof

class QuantumZKP:
    def __init__(self, dimensions: int = 8, security_level: int = 128):
        self.dimensions = dimensions
        self.security_level = security_level
        logger.debug("Initialized QuantumZKP instance")

    def prove_vector_knowledge_batch(self, vectors: List[np.ndarray], identifiers: List[str]) -> List[Tuple[bytes, Dict]]:
        # Warming up the cache for JIT and joblib parallel processing
        self._warm_up_cache(vectors[:10], identifiers[:10])

        results = Parallel(n_jobs=-1, batch_size=10)(
            delayed(prove_vector_knowledge_worker)(vector, identifier, self.dimensions, self.security_level)
            for vector, identifier in zip(vectors, identifiers)
        )
        return results

    def _warm_up_cache(self, vectors, identifiers):
        # Run a warm-up pass to compile and cache the results of JIT functions
        for vector, identifier in zip(vectors, identifiers):
            _ = prove_vector_knowledge_worker(vector, identifier, self.dimensions, self.security_level)

# Performance testing code
if __name__ == "__main__":
    zk_proof_system = QuantumZKP()
    num_vectors = 100000  # Large number of vectors for testing cache performance
    vector_size = 8

    rng = np.random.default_rng(time.time_ns())
    vectors = [rng.random(vector_size) for _ in range(num_vectors)]
    identifiers = [f"identifier_{i}" for i in range(num_vectors)]

    # Perform initial warm-up
    zk_proof_system.prove_vector_knowledge_batch(vectors[:10], identifiers[:10])

    start_time = time.time()
    commitments_proofs = zk_proof_system.prove_vector_knowledge_batch(vectors, identifiers)
    end_time = time.time()
    proving_time = end_time - start_time
    proofs_per_second = num_vectors / proving_time

    print(f"Generated {num_vectors} proofs in {proving_time:.2f} seconds.")
    print(f"Proof generation rate: {proofs_per_second:.2f} proofs per second.")
