import secrets
from cryptography.hazmat.primitives.asymmetric import ed25519

from oqs import Signature, KeyEncapsulation  # Import Falcon from oqs-python
from sympy import symbols, Poly, GF
from typing import List, Tuple
import numpy as np
from mpmath import mp


class VSS:
    PRIME_MODULUS = 2 ** 127 - 1
    SCALE_FACTOR = 10 ** 8  # Adjusted scale factor for consistent precision

    def __init__(self):
        # Initialize Kyber and Falcon for key exchange and signing
        self.threshold = 3
        self.kyber = KeyEncapsulation('Kyber512')
        self.falcon = Signature("Falcon-512")
        self.falcon_public_key = self.falcon.generate_keypair()  # Generate Falcon public key
        self.falcon_private_key = self.falcon.export_secret_key()

    def split_secret(self, coordinates: np.ndarray, threshold: int, num_shares: int) -> List[
        List[Tuple[int, bytes, bytes, bytes]]]:
        all_shares = []

        # Verify dimensionality of coordinates
       # if len(coordinates) != 3:
        #    raise ValueError("Coordinates array must be 3-dimensional.")

        for coord in coordinates:
            high_precision_coord = mp.mpf(coord)
            coord_int = int(high_precision_coord * self.SCALE_FACTOR)

            # Generate Shamir shares for this coordinate
            x = symbols('x')
            coefficients = [coord_int] + [secrets.randbelow(self.PRIME_MODULUS) for _ in range(threshold - 1)]
            polynomial = Poly.from_list(coefficients, x, domain=GF(self.PRIME_MODULUS))

            # Encrypt and sign shares
            coord_shares = []
            for i in range(1, num_shares + 1):
                share_value = polynomial.eval(i) % self.PRIME_MODULUS
                public_key = self.kyber.generate_keypair()  # Generate a Kyber public key for encryption
                ciphertext, shared_secret = self.kyber.encap_secret(public_key)
                signature = self.falcon.sign(ciphertext)
                coord_shares.append((i, ciphertext, shared_secret, signature))

            all_shares.append(coord_shares)

        return all_shares

    def reconstruct_secret(self, all_encrypted_shares, public_key):
        reconstructed_coords = []
        if len(all_encrypted_shares) < self.threshold:
            raise ValueError("Not enough shares provided for reconstruction.")
        for coord_shares in all_encrypted_shares:
            shares_for_reconstruction = []
            for i, ciphertext, encrypted_share, signature in coord_shares:
                if not self.falcon.verify(ciphertext, signature, public_key):
                    raise ValueError("Signature verification failed for share.")
                shared_secret = self.kyber.decap_secret(ciphertext)
                share_int = int.from_bytes(shared_secret, byteorder='big')
                shares_for_reconstruction.append((i, share_int))

            # Perform Lagrange interpolation and scale back
            coord_int = self._reconstruct_from_shares(shares_for_reconstruction)
            coord = round(float(mp.mpf(coord_int) / self.SCALE_FACTOR), 4)  # Consistent rounding precision
            reconstructed_coords.append(coord)

        return np.array(reconstructed_coords)

    def _reconstruct_from_shares(self, shares: List[Tuple[int, int]], modulus: int = PRIME_MODULUS) -> int:
        """
        Use Lagrange interpolation to reconstruct the secret integer from shares.

        Parameters:
            shares (List[Tuple[int, int]]): List of (x, y) points for interpolation.
            modulus (int): Prime modulus for finite field operations.

        Returns:
            int: The reconstructed secret integer.
        """

        def lagrange_interpolate(x: int, x_s: List[int], y_s: List[int], p: int) -> int:
            """Perform Lagrange interpolation at x=0 over a finite field with a prime modulus."""
            k = len(x_s)
            result = 0
            for j in range(k):
                term = y_s[j]
                for m in range(k):
                    if m != j:
                        denom = (x_s[j] - x_s[m]) % p
                        if denom == 0:
                            raise ValueError("Non-invertible base in modular interpolation")
                        term = (term * (x - x_s[m]) * pow(denom, -1, p)) % p
                result = (result + term) % p
            return result

        x_vals, y_vals = zip(*shares)
        return lagrange_interpolate(0, x_vals, y_vals, modulus)
