import base64
import json
import os
from os.path import dirname


import blake3
import geoip2.database
import numpy as np

from src.modules.zkp import QuantumZKP
from src.modules.crypto_module.key_management import KeyManagement
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class AddressManager:
    def __init__(self):
        self.key_management = KeyManagement()  # Key management for encryption and signing
        self.zkp = QuantumZKP(dimensions=8, security_level=128)  # ZKP for address validation
        logger.info("Initialized AddressManager")

    def generate_geohashed_address(self, ip_address: str, purpose: str, return_data=False):
        """Generate an address with GeoIP information, ZKP for location verification, and purpose differentiation."""
        dir1 = os.path.join(dirname(__file__), 'vendor/GeoLite2-City.mmdb')
        try:
            with geoip2.database.Reader(dir1) as reader:
                response = reader.city(ip_address)
                location_data = {
                    "latitude": response.location.latitude,
                    "longitude": response.location.longitude,
                    "country": response.country.iso_code,
                    "city": response.city.name
                }
                # Create a Blake3 hash of the location data
                location_hash = blake3.blake3(json.dumps(location_data).encode('utf-8')).hexdigest()

                # Generate a ZKP witness for the location
                identifier = f"geo_{ip_address}"
                vector = np.array([response.location.latitude, response.location.longitude] + [0.0] * 6)
                commitment, proof = self.zkp.prove_vector_knowledge(vector, identifier)

                # Convert `commitment` and `proof` to JSON serializable formats
                commitment_serializable = commitment.hex()
                proof_serializable = {k: (v.hex() if isinstance(v, bytes) else v) for k, v in proof.items()}

                # Encrypt the location hash, ZKP proof, and purpose
                combined_data = json.dumps({
                    "location_hash": location_hash,
                    "zkp_proof": {
                        "commitment": commitment_serializable,
                        "proof": proof_serializable
                    },
                    "purpose": purpose
                }).encode('utf-8')
                encrypted_data = self.key_management.encrypt(combined_data)

                # Use base64 to encode the encrypted data
                encoded_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
                address_hash = blake3.blake3(encoded_data.encode('utf-8')).hexdigest()

                # Generate the address with a specific prefix
                address_prefix = "AXM"
                address = f"{address_prefix}_{address_hash}"
                if return_data:
                    return address, {'vector': vector}
                else:
                    return address
        except Exception as e:
            logger.error(f"Error generating geohashed address: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    manager = AddressManager()
    try:
        address = manager.generate_geohashed_address("8.8.8.8", "wallet")
        print(f"Generated Address: {address}")
    except Exception as e:
        print(f"Failed to generate address: {e}")
