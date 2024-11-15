import json
import numpy as np
import hashlib
import logging
import time
import os
import psutil
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import dataclass, field
from oqs import Signature
from joblib import Parallel, delayed
from numba import njit, prange, cuda
from functools import lru_cache
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import asyncio
import warnings
from collections import deque

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Constants
MAX_VECTOR_SIZE = 1024
ENTROPY_EPSILON = 1e-10
PROBABILITY_TOLERANCE = 1e-5
DEFAULT_BATCH_SIZE = 1000
MAX_CACHE_SIZE = 10000
THREAD_COUNT = min(32, (os.cpu_count() or 1) * 4)

# Initialize thread pool
THREAD_POOL = ThreadPoolExecutor(max_workers=THREAD_COUNT)


# CPU Affinity Setup
def set_cpu_affinity():
    try:
        process = psutil.Process()
        process.cpu_affinity(list(range(psutil.cpu_count())))
    except Exception as e:
        logger.warning(f"Could not set CPU affinity: {e}")


# GPU Support Check
USE_GPU = cuda.is_available()
if USE_GPU:
    logger.info("CUDA GPU support enabled")


@njit(parallel=True, fastmath=True)
def adjust_to_square_length(vector: np.ndarray) -> np.ndarray:
    """Optimized vector length adjustment using parallel processing."""
    target_length = int(np.ceil(np.sqrt(len(vector))) ** 2)
    if len(vector) < target_length:
        result = np.zeros(target_length, dtype=vector.dtype)
        for i in prange(len(vector)):
            result[i] = vector[i]
        return result
    return vector


@njit(fastmath=True)
def calculate_entropy(amplitudes: np.ndarray) -> float:
    """Optimized entropy calculation using Numba."""
    probabilities = np.abs(amplitudes) ** 2
    log_probs = np.log2(probabilities + ENTROPY_EPSILON)
    return -np.sum(probabilities * log_probs)


@dataclass
class QuantumStateVector:
    coordinates: np.ndarray
    entanglement: float = field(default=0.0)
    coherence: float = field(default=1.0)
    state_type: str = field(default="SUPERPOSITION")
    timestamp: float = field(default_factory=lambda: time.time())
    _cache: Dict = field(default_factory=dict)
    basis_coefficients_cache: Optional[np.ndarray] = field(default=None)

    def __post_init__(self):
        if len(self.coordinates) > MAX_VECTOR_SIZE:
            warnings.warn(f"Vector size exceeds MAX_VECTOR_SIZE ({MAX_VECTOR_SIZE})")

    @lru_cache(maxsize=1024)
    def calculate_coherence(self) -> float:
        if 'coherence' not in self._cache:
            self._cache['coherence'] = float(np.mean(np.abs(self.coordinates)))
        return self._cache['coherence']

    def serialize(self) -> bytes:
        if 'serialized' not in self._cache:
            data = {
                "coordinates": self.coordinates.tolist(),
                "entanglement": self.entanglement,
                "coherence": self.coherence,
                "state_type": self.state_type,
                "timestamp": self.timestamp
            }
            self._cache['serialized'] = json.dumps(data, separators=(',', ':'))
        return self._cache['serialized'].encode('utf-8')

    def clear_cache(self):
        self._cache.clear()
        if hasattr(self.calculate_coherence, 'cache_clear'):
            self.calculate_coherence.cache_clear()


class ResultCache:
    """Thread-safe cache for computation results."""

    def __init__(self, maxsize: int = MAX_CACHE_SIZE):
        self.cache = {}
        self.maxsize = maxsize
        self.lock = threading.Lock()
        self.access_times = {}
        self.access_queue = deque()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                self.access_queue.append(key)
                return self.cache[key]
        return None

    def put(self, key: str, value: Any):
        with self.lock:
            if len(self.cache) >= self.maxsize:
                self._evict_oldest()
            self.cache[key] = value
            self.access_times[key] = time.time()
            self.access_queue.append(key)

    def _evict_oldest(self):
        while self.access_queue and len(self.cache) >= self.maxsize:
            oldest_key = self.access_queue.popleft()
            if oldest_key in self.cache:
                del self.cache[oldest_key]
                del self.access_times[oldest_key]




class QuantumZKP:
    def __init__(self, dimensions: int = 8, security_level: int = 128):
        set_cpu_affinity()

        self.dimensions = min(dimensions, MAX_VECTOR_SIZE)
        self.security_level = security_level
        self._falcon = Signature("Falcon-512")
        self.public_key = self._falcon.generate_keypair()

        # Initialize caches and buffers
        self._result_cache = ResultCache()
        self._batch_buffer = queue.Queue()
        self._thread_local = threading.local()

        logger.info(f"Initialized QuantumZKP with dimensions={dimensions}, "
                    f"security_level={security_level}, GPU_enabled={USE_GPU}")

    def _get_thread_local_hasher(self):
        """Get or create thread-local hasher instance."""
        if not hasattr(self._thread_local, 'hasher'):
            self._thread_local.hasher = hashlib.sha3_256()
        return self._thread_local.hasher

    @staticmethod
    @cuda.jit
    def _gpu_calculate_entropy(amplitudes, result):
        """GPU-accelerated entropy calculation."""
        idx = cuda.grid(1)
        if idx < amplitudes.size:
            prob = abs(amplitudes[idx]) ** 2
            if prob > ENTROPY_EPSILON:
                result[idx] = -prob * np.log2(prob)

    def _calculate_entanglement_entropy(self, amplitudes: np.ndarray) -> float:
        """Calculate entropy using GPU if available, fallback to CPU."""
        if USE_GPU and len(amplitudes) > 1000:
            result = np.zeros_like(amplitudes, dtype=np.float64)
            threadsperblock = 256
            blockspergrid = (amplitudes.size + threadsperblock - 1) // threadsperblock
            self._gpu_calculate_entropy[blockspergrid, threadsperblock](amplitudes, result)
            return float(np.sum(result))
        else:
            return calculate_entropy(amplitudes)

    @staticmethod
    @njit(parallel=True, fastmath=True)
    def _generate_measurements(state_coordinates: np.ndarray, security_level: int) -> List[Dict]:
        """Vectorized measurement generation."""
        num_measurements = security_level // 8
        measurements = []

        for i in prange(num_measurements):
            idx = np.random.randint(0, len(state_coordinates))
            amplitude = state_coordinates[idx]
            probability = float(np.abs(amplitude) ** 2)
            phase = float(np.angle(amplitude))

            measurements.append({
                'basis_index': idx,
                'probability': probability,
                'phase': phase
            })

        return measurements

    def _generate_commitment(self, state: QuantumStateVector, identifier: str) -> bytes:
        """Thread-safe commitment generation."""
        hasher = self._get_thread_local_hasher()
        hasher.update(state.coordinates.tobytes())
        hasher.update(str(state.coherence).encode())
        hasher.update(identifier.encode())
        commitment = hasher.digest()
        hasher.clear()
        return commitment

    async def prove_vector_knowledge(self, vector: np.ndarray, identifier: str) -> Tuple[bytes, Dict]:
        """Asynchronous proof generation."""
        # Normalize vector
        vector = vector / np.linalg.norm(vector)

        # Create quantum state
        state = QuantumStateVector(vector)
        state.calculate_coherence()

        # Calculate entropy and commitment
        entropy = await asyncio.to_thread(self._calculate_entanglement_entropy, state.coordinates)
        commitment = await asyncio.to_thread(self._generate_commitment, state, identifier)

        # Generate measurements
        measurements = await asyncio.to_thread(
            self._generate_measurements,
            state.coordinates,
            self.security_level
        )

        # Create proof
        proof = {
            'quantum_dimensions': self.dimensions,
            'basis_coefficients': state.coordinates.tolist(),
            'measurements': measurements,
            'state_metadata': {
                'coherence': state.coherence,
                'entanglement': entropy,
                'timestamp': time.time()
            },
            'identifier': identifier
        }

        # Sign proof
        message = await asyncio.to_thread(
            self._prepare_message_for_signing,
            proof,
            commitment
        )
        signature = await asyncio.to_thread(self._falcon.sign, message)
        proof['signature'] = signature.hex()

        return commitment, proof

    async def prove_vector_knowledge_batch(
            self,
            vectors: List[np.ndarray],
            identifiers: List[str],
            batch_size: int = DEFAULT_BATCH_SIZE
    ) -> List[Tuple[bytes, Dict]]:
        """Asynchronous batch proof generation."""
        results = []

        async def process_batch(batch_vectors, batch_ids):
            tasks = []
            for vector, id_ in zip(batch_vectors, batch_ids):
                tasks.append(self.prove_vector_knowledge(vector, id_))
            return await asyncio.gather(*tasks)

        # Process in batches
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i + batch_size]
            batch_ids = identifiers[i:i + batch_size]
            batch_results = await process_batch(batch_vectors, batch_ids)
            results.extend(batch_results)

        return results

    def verify_proof(self, commitment: bytes, proof: Dict, identifier: str) -> bool:
        """Verify a single proof."""
        try:
            # Quick validation checks
            if not self._validate_proof_structure(proof):
                return False

            # Cache check
            cache_key = f"{commitment.hex()}-{identifier}"
            cached_result = self._result_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Verify signature
            signature = bytes.fromhex(proof['signature'])
            message = self._prepare_message_for_signing(proof, commitment)
            if not self._falcon.verify(message, signature, self.public_key):
                return False

            # Verify basis coefficients
            coefficients = np.array([
                complex(c) if isinstance(c, (int, float))
                else complex(c['real'], c['imag'])
                for c in proof['basis_coefficients']
            ])

            if not self._verify_basis_coefficients(coefficients):
                return False

            # Cache result
            self._result_cache.put(cache_key, True)
            return True

        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            return False

    def verify_proof_batch(
            self,
            commitments_proofs_ids: List[Tuple[bytes, Dict, str]],
            batch_size: int = DEFAULT_BATCH_SIZE
    ) -> List[bool]:
        """Optimized batch verification."""
        results = []

        def verify_batch(batch):
            with THREAD_POOL as executor:
                futures = [
                    executor.submit(self.verify_proof, *item)
                    for item in batch
                ]
                return [future.result() for future in concurrent.futures.as_completed(futures)]

        # Process in batches
        for i in range(0, len(commitments_proofs_ids), batch_size):
            batch = commitments_proofs_ids[i:i + batch_size]
            results.extend(verify_batch(batch))

        return results

    def _validate_proof_structure(self, proof: Dict) -> bool:
        """Validate proof structure."""
        required_fields = {
            'quantum_dimensions',
            'basis_coefficients',
            'measurements',
            'state_metadata',
            'signature',
            'identifier'
        }
        return all(field in proof for field in required_fields)

    @staticmethod
    @njit(parallel=True, fastmath=True)
    def _verify_basis_coefficients(coefficients: np.ndarray) -> bool:
        """Vectorized coefficient verification."""
        total = 0.0
        for i in prange(len(coefficients)):
            total += abs(coefficients[i]) ** 2
        return abs(total - 1.0) < PROBABILITY_TOLERANCE

    def _prepare_message_for_signing(self, proof: Dict, commitment: bytes) -> bytes:
        """Prepare message for signing."""
        proof_copy = {k: v for k, v in proof.items() if k != "signature"}
        message = json.dumps(
            proof_copy,
            sort_keys=True,
            default=self._complex_encoder,
            separators=(',', ':')
        ).encode('utf-8')
        return message + commitment

    @staticmethod
    def _complex_encoder(obj):
        """JSON encoder for complex numbers."""
        if isinstance(obj, complex):
            return {'real': obj.real, 'imag': obj.imag}
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def cleanup(self):
        """Cleanup resources."""
        try:
            THREAD_POOL.shutdown(wait=True)
            self._result_cache = ResultCache()  # Reset cache
            self._batch_buffer = queue.Queue()  # Reset buffer
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")