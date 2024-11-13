import concurrent.futures
import logging
import unittest
import numpy as np
import time
from typing import List
from zkp.qzkp_optimized import logger, QuantumStateVector, QuantumZKP


class TestQuantumZKP(unittest.TestCase):
    def setUp(self):
        self.qzkp = QuantumZKP(dimensions=9, security_level=128)
        self.vector = np.random.rand(self.qzkp.dimensions)
        self.identifier = "test_id"

    def test_proof_generation(self):
        commitment, proof = self.qzkp.prove_vector_knowledge(self.vector, self.identifier)
        self.assertIn('quantum_dimensions', proof)
        self.assertIn('basis_coefficients', proof)
        self.assertIn('measurements', proof)
        self.assertIn('state_metadata', proof)
        self.assertIn('signature', proof)

    def test_commitment_consistency(self):
        commitment1, _ = self.qzkp.prove_vector_knowledge(self.vector, self.identifier)
        commitment2, _ = self.qzkp.prove_vector_knowledge(self.vector, self.identifier)
        self.assertEqual(commitment1, commitment2)

   # def test_entanglement_calculation(self):
   #     known_state = np.ndarray([1, 0, 0, 0, 0, 0, 0, 0, 0])
   #     entanglement = self.qzkp._calculate_entanglement(known_state)
        #self.assertAlmostEqual(entanglement, 0.0, places=2)

    def test_measurement_generation(self):
        state = QuantumStateVector(self.vector)
        measurements = self.qzkp._generate_measurements(state)
        self.assertEqual(len(measurements), self.qzkp.security_level // 8)
        for measurement in measurements:
            self.assertIn('basis_index', measurement)
            self.assertIn('probability', measurement)
            self.assertIn('phase', measurement)

    def test_signature_verification(self):
        # Normalize the vector to ensure consistent state for deterministic testing
        self.vector = self.vector / np.linalg.norm(self.vector)
        commitment, proof = self.qzkp.prove_vector_knowledge(self.vector, self.identifier)

        # Log intermediate values to examine proof structure
        logger.debug(f"Generated Commitment: {commitment}")
        logger.debug(f"Generated Proof: {proof}")

        # Call the verify_proof function
        valid = self.qzkp.verify_proof(commitment, proof, self.identifier)

        # Detailed logging if verification fails
        if not valid:
            logger.debug("Verification failed during test_signature_verification.")
            logger.debug(f"Commitment: {commitment}")
            logger.debug(f"Proof: {proof}")
            logger.debug(f"Identifier: {self.identifier}")

        # Check if the proof is valid
        self.assertTrue(valid, "Signature verification failed; check debug logs for discrepancies.")

    def test_batch_proof_generation_performance(self):
        batch_size = 100
        vectors = [np.random.rand(self.qzkp.dimensions) for _ in range(batch_size)]
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(
                executor.map(lambda v: self.qzkp.prove_vector_knowledge(v, self.identifier),
                             vectors))

        duration = time.time() - start_time
        print(f"Batch proof generation for {batch_size} vectors took {duration:.2f} seconds.")

    def test_batch_verification_performance(self):
        batch_size = 100
        vectors = [np.random.rand(self.qzkp.dimensions) for _ in range(batch_size)]
        proofs = []

        for vector in vectors:
            commitment, proof = self.qzkp.prove_vector_knowledge(vector, self.identifier)
            proofs.append((commitment, proof))

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda cp: self.qzkp.verify_proof(cp[0], cp[1], self.identifier), proofs))

        duration = time.time() - start_time
        failed_indices = [i for i, result in enumerate(results) if not result]

        print(f"Batch verification for {batch_size} proofs took {duration:.2f} seconds.")
        print(f"Failed verifications at indices: {failed_indices}")

        if not all(results):
            logger.debug("Some proofs failed verification.")
            for idx in failed_indices[:1]:  # Log details for first failed proof for readability
                commitment, proof = proofs[idx]
                self.qzkp.verify_proof(commitment, proof, self.identifier)  # Triggers detailed logging

        self.assertTrue(all(results), "Some batch verifications failed.")

    def test_cached_entanglement_performance(self):
        amplitudes = np.random.rand(self.qzkp.dimensions)
        start_time = time.time()

        for _ in range(1000):
            self.qzkp._calculate_entanglement(amplitudes)

        duration = time.time() - start_time
        print(f"Cached entanglement calculation for 1000 calls took {duration:.2f} seconds.")

    def test_cached_basis_coefficients_performance(self):
        vector = tuple(np.random.rand(self.qzkp.dimensions))
        start_time = time.time()

        for _ in range(1000):
            self.qzkp._cached_basis_coefficients(vector)

        duration = time.time() - start_time
        print(f"Cached basis coefficient calculation for 1000 calls took {duration:.2f} seconds.")


if __name__ == "__main__":
    unittest.main()
