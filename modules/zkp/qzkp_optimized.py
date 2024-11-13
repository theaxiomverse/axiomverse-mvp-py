import json
import numpy as np
import hashlib
import logging
import time
from typing import Tuple, List, Dict
from dataclasses import dataclass
from oqs import Signature  # Ensure 'oqs-python' is installed
from joblib import Parallel, delayed
from numba import njit  # For performance optimization
import sys

l = logging.getLogger()
l.setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


# Utility function for adjusting vector lengths
def adjust_to_square_length(vector: np.ndarray) -> np.ndarray:
    target_length = int(np.ceil(np.sqrt(len(vector))) ** 2)
    if len(vector) < target_length:
        return np.pad(vector, (0, target_length - len(vector)), constant_values=0)
    return vector

@njit
def calculate_entropy(amplitudes: np.ndarray) -> float:
    probabilities = np.abs(amplitudes) ** 2
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    return entropy

@dataclass
class QuantumStateVector:
    coordinates: np.ndarray
    entanglement: float
    coherence: float
    state_type: str
    timestamp: float

    def __init__(self, state_vector: np.ndarray, deterministic: bool = False):
        state_vector = adjust_to_square_length(state_vector)
        if deterministic:
            phase = np.zeros(len(state_vector))
        else:
            phase = np.random.uniform(0, 2 * np.pi, len(state_vector))
        # Combine amplitude and phase into a complex number
        self.coordinates = state_vector * np.exp(1j * phase)
        self.entanglement = 0.0
        self.coherence = 1.0
        self.state_type = "SUPERPOSITION"
        self.timestamp = 0.0 if deterministic else time.time()

    def calculate_coherence(self):
        self.coherence = np.mean(np.abs(self.coordinates))

    def serialize(self):
        return json.dumps({
            "coordinates": [complex(c).real for c in self.coordinates],
            "entanglement": self.entanglement,
            "coherence": self.coherence,
            "state_type": self.state_type,
            "timestamp": self.timestamp
        }, separators=(',', ':')).encode('utf-8')

class QuantumZKP:
    def __init__(self, dimensions: int = 8, security_level: int = 128):
        self.dimensions = dimensions
        self.security_level = security_level
        self._falcon = Signature("Falcon-512")
        self.public_key = self._falcon.generate_keypair()
        logger.debug("Initialized QuantumZKP instance")

    @staticmethod
    @njit
    def _calculate_entanglement_entropy(amplitudes: np.ndarray) -> float:
        return calculate_entropy(amplitudes)

    @staticmethod
    def _purity_entropy_correlation(entropy: float, coherence: float) -> float:
        # Purity is always 1 for normalized state vectors
        correlation = entropy  # Since purity is 1
        logger.info(f"Entropy: {entropy:.6f} for coherence {coherence:.4f}")
        return correlation

    @staticmethod
    def _generate_measurements(state_coordinates: np.ndarray, security_level: int) -> List[Dict]:
        """Generate simulated measurements with vectorized operations."""
        num_measurements = security_level // 8
        basis_indices = np.random.randint(0, len(state_coordinates), size=num_measurements)
        amplitudes = state_coordinates[basis_indices]
        probabilities = np.abs(amplitudes) ** 2
        phases = np.angle(amplitudes)

        measurements = [
            {'basis_index': int(idx), 'probability': float(prob), 'phase': float(phase)}
            for idx, prob, phase in zip(basis_indices, probabilities, phases)
        ]
        logger.debug(f"Generated measurements: {measurements}")
        return measurements

    @staticmethod
    def _generate_commitment(state: QuantumStateVector, identifier: str) -> bytes:
        h = hashlib.sha3_256()
        h.update(state.coordinates.tobytes())
        h.update(str(state.coherence).encode())
        h.update(identifier.encode())
        return h.digest()

    @staticmethod
    def _prepare_message_for_signing(proof: dict, commitment: bytes) -> bytes:
        proof_copy = {k: v for k, v in proof.items() if k != "signature"}
        serialized_message = json.dumps(
            proof_copy, sort_keys=True, default=QuantumZKP._complex_encoder, separators=(',', ':')
        ).encode('utf-8')
        return serialized_message + commitment

    @staticmethod
    def _complex_encoder(obj):
        if isinstance(obj, complex):
            return {'real': obj.real, 'imag': obj.imag}
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def prove_vector_knowledge(self, vector: np.ndarray, identifier: str) -> Tuple[bytes, Dict]:
        vector = vector / np.linalg.norm(vector)
        # Set deterministic=True to eliminate random phases
        state = QuantumStateVector(vector, deterministic=True)
        state.calculate_coherence()
        entropy = self._calculate_entanglement_entropy(state.coordinates)
        correlation = self._purity_entropy_correlation(entropy, state.coherence)
        commitment = self._generate_commitment(state, identifier)

        # Directly assign basis coefficients
        state.basis_coefficients_cache = state.coordinates.tolist()

        measurements = self._generate_measurements(state.coordinates, self.security_level)
        proof = {
            'quantum_dimensions': self.dimensions,
            'basis_coefficients': [complex(c) for c in state.basis_coefficients_cache],
            'measurements': measurements,
            'state_metadata': {
                'coherence': state.coherence,
                'entanglement': entropy,
                'correlation': correlation
            },
            'identifier': identifier
        }

        # Sign the message using the main Signature object
        message = self._prepare_message_for_signing(proof, commitment)
        signature = self._falcon.sign(message)
        proof['signature'] = signature.hex()
        return commitment, proof

    def verify_proof(self, commitment: bytes, proof: Dict, identifier: str) -> bool:
        try:
            required_fields = {'quantum_dimensions', 'basis_coefficients', 'measurements',
                               'state_metadata', 'signature', 'identifier'}
            if not all(field in proof for field in required_fields):
                return False
            if proof['quantum_dimensions'] != self.dimensions or proof['identifier'] != identifier:
                return False

            signature = bytes.fromhex(proof['signature'])
            message = self._prepare_message_for_signing(proof, commitment)
            # Verify using the main Signature object
            if not self._falcon.verify(message, signature, self.public_key):
                return False

            basis_coefficients = [
                complex(c['real'], c['imag']) if isinstance(c, dict) else complex(c)
                for c in proof['basis_coefficients']
            ]
            total_probability = np.sum(np.abs(basis_coefficients) ** 2)
            return np.isclose(total_probability, 1.0, atol=1e-5)
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            return False

    # Implement batch processing using threading
    def prove_vector_knowledge_batch(self, vectors: List[np.ndarray], identifiers: List[str]) -> List[Tuple[bytes, Dict]]:
        # Prepare arguments for worker functions
        args_list = [
            (vector, identifier)
            for vector, identifier in zip(vectors, identifiers)
        ]

        results = Parallel(n_jobs=-1, backend='threading')(
            delayed(self._prove_vector_knowledge_worker)(args)
            for args in args_list
        )
        return results

    def _prove_vector_knowledge_worker(self, args):
        vector, identifier = args
        return self.prove_vector_knowledge(vector, identifier)

    def verify_proof_batch(self, commitments_proofs_ids: List[Tuple[bytes, Dict, str]]) -> List[bool]:
        args_list = [
            (commitment, proof, identifier)
            for commitment, proof, identifier in commitments_proofs_ids
        ]

        results = Parallel(n_jobs=-1, backend='threading')(
            delayed(self._verify_proof_worker)(args)
            for args in args_list
        )
        return results

    def _verify_proof_worker(self, args):
        commitment, proof, identifier = args
        return self.verify_proof(commitment, proof, identifier)

# Performance testing code
if __name__ == "__main__":
    zk_proof_system = QuantumZKP()
    num_vectors = 100000  # Number of vectors to test with; adjust as needed
    vector_size = 8     # Size of each vector

    rng = np.random.default_rng(time.time_ns())
    vectors = [rng.random(vector_size) for _ in range(num_vectors)]
    identifiers = [f"identifier_{i}" for i in range(num_vectors)]

    # Warm-up run to initialize JIT compilation and cache
    zk_proof_system.prove_vector_knowledge_batch(vectors[:10], identifiers[:10])
    commitments_proofs_ids_warmup = [
        (commitment, proof, identifier)
        for (commitment, proof), identifier in zip(
            zk_proof_system.prove_vector_knowledge_batch(vectors[:10], identifiers[:10]),
            identifiers[:10]
        )
    ]
    zk_proof_system.verify_proof_batch(commitments_proofs_ids_warmup)

    # Measure proof generation performance
    start_time = time.time()
    commitments_proofs = zk_proof_system.prove_vector_knowledge_batch(vectors, identifiers)
    end_time = time.time()
    proving_time = end_time - start_time
    proofs_per_second = num_vectors / proving_time

    print(f"Generated {num_vectors} proofs in {proving_time:.2f} seconds.")
    print(f"Proof generation rate: {proofs_per_second:.2f} proofs per second.")

    # Prepare data for batch verification
    commitments_proofs_ids = [
        (commitment, proof, identifier)
        for (commitment, proof), identifier in zip(commitments_proofs, identifiers)
    ]

    # Measure proof verification performance
    start_time = time.time()
    verification_results = zk_proof_system.verify_proof_batch(commitments_proofs_ids)
    end_time = time.time()
    verification_time = end_time - start_time
    verifications_per_second = num_vectors / verification_time

    print(f"Verified {num_vectors} proofs in {verification_time:.2f} seconds.")
    print(f"Proof verification rate: {verifications_per_second:.2f} proofs per second.")

    # Check if all verifications passed
    all_verified = all(verification_results)
    print(f"All proofs verified successfully: {all_verified}")
    time.sleep(60)  
