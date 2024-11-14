from oqs import Signature
import base64

class SignatureManagement:
    def __init__(self):
        self._falcon = Signature("Falcon-512")
    def sign_data(self, secret_key: str, data: str) -> str:
        """Sign the given data using Kyber-512 secret key."""
        sk = base64.b64decode(secret_key.encode())
        signature = self._falcon.sign(data.encode())
        return base64.b64encode(signature).decode()

    def verify_signature(self, public_key: str, data: str, signature: str) -> bool:
        """Verify the signature of the data using Kyber-512 public key."""
        pk = base64.b64decode(public_key.encode())
        signature_bytes = base64.b64decode(signature.encode())
        return self._falcon.verify(data.encode(), signature_bytes, pk)

# Example usage:
# signature_mgmt = SignatureManagement()
# signed_data = signature_mgmt.sign_data(sk, "my_contract_data")
# valid = signature_mgmt.verify_signature(pk, "my_contract_data", signed_data)
