
# **AxiomVerse Address Generation Process Documentation**

## **Overview**

The `AddressManager` class is responsible for generating geohashed addresses that incorporate:

- **GeoIP Information**: Geographical data associated with an IP address.
- **Zero-Knowledge Proof (ZKP)**: Cryptographic proof to validate location data without revealing the actual data.
- **Encryption**: Securing the combined data using encryption techniques.
- **Purpose Differentiation**: Associating the address with a specific purpose (e.g., "wallet", "email").

The generated address includes a hash of the encrypted data, ensuring uniqueness and security.

---

## **Process Flow**

1. **Initialization**:
   - Instantiate `KeyManagement` for encryption and signing.
   - Instantiate `QuantumZKP` for generating ZKP proofs.
   
2. **GeoIP Data Retrieval**:
   - Use the provided IP address to fetch geographical data (latitude, longitude, country, city) using the GeoIP database.

3. **Location Data Hashing**:
   - Serialize the location data to JSON and hash it using the Blake3 hashing algorithm to create a `location_hash`.

4. **ZKP Proof Generation**:
   - Construct a vector from the location coordinates, padded to match the required dimensions.
   - Generate a ZKP proof for the vector using the `QuantumZKP` class.

5. **ZKP Proof Serialization**:
   - Convert the ZKP proof into a JSON-serializable format, handling byte data appropriately.

6. **Data Encryption**:
   - Combine the `location_hash`, serialized ZKP proof, and purpose into a single data object.
   - Serialize the combined data to JSON and encrypt it using the `KeyManagement` class.

7. **Address Creation**:
   - Base64-encode the encrypted data to ensure safe transmission.
   - Hash the encoded data using Blake3 to produce the final address hash.
   - Prepend a specific prefix (e.g., "AXM") to the address hash to form the complete address.

---

## **Detailed Steps**

### **1. Initialization**

```python
def __init__(self):
    self.key_management = KeyManagement()
    self.zkp = QuantumZKP(dimensions=8, security_level=128)
    logger.info("Initialized AddressManager")
```

- **KeyManagement**:
  - Manages encryption keys and provides methods for encryption and decryption.
  
- **QuantumZKP**:
  - Handles the creation of zero-knowledge proofs for quantum state vectors.
  - Configured with 8 dimensions and a security level of 128 bits.

### **2. GeoIP Data Retrieval**

```python
with geoip2.database.Reader(geoip_database_path) as reader:
    response = reader.city(ip_address)
    location_data = {
        "latitude": response.location.latitude,
        "longitude": response.location.longitude,
        "country": response.country.iso_code,
        "city": response.city.name
    }
```

- **GeoIP Database**:
  - Provides geographical information based on the IP address.
  - The database file `GeoLite2-City.mmdb` is required and should be located in the specified path.

- **Location Data**:
  - Extracted fields include latitude, longitude, country ISO code, and city name.
  - This data is essential for both hashing and ZKP proof generation.

### **3. Location Data Hashing**

```python
location_hash = blake3.blake3(json.dumps(location_data).encode('utf-8')).hexdigest()
```

- **Purpose**:
  - Hashing the location data ensures data integrity and prevents tampering.
  - The hash acts as a unique identifier for the location data without revealing the actual values.

- **Blake3 Hashing Algorithm**:
  - A cryptographic hash function known for its speed and security.
  - Produces a 256-bit hash value.

### **4. ZKP Proof Generation**

```python
identifier = f"geo_{ip_address}"
vector = np.array([response.location.latitude, response.location.longitude] + [0.0] * 6)
zkp_proof = self.zkp.prove_vector_knowledge(vector, identifier)
```

- **Vector Construction**:
  - The vector includes the latitude and longitude, padded with zeros to match the required 8 dimensions.
  - The padding ensures compatibility with the `QuantumZKP` class configuration.

- **Identifier**:
  - A unique identifier combining the prefix "geo_" with the IP address.
  - Used in the ZKP proof generation process.

- **ZKP Proof**:
  - The `prove_vector_knowledge` method generates a proof that you know the vector without revealing it.
  - This allows others to verify the proof without accessing the actual location data.

### **5. ZKP Proof Serialization**

```python
if isinstance(zkp_proof, dict):
    zkp_proof_serializable = {k: v.hex() if isinstance(v, bytes) else v for k, v in zkp_proof.items()}
elif isinstance(zkp_proof, bytes):
    zkp_proof_serializable = zkp_proof.hex()
else:
    zkp_proof_serializable = str(zkp_proof)
```

- **Purpose**:
  - Convert the ZKP proof into a format suitable for JSON serialization.
  - Handles different data types within the proof, particularly byte data.

- **Serialization Handling**:
  - Byte values are converted to hexadecimal strings.
  - Other values are left as-is or converted to strings.

### **6. Data Encryption**

```python
combined_data = json.dumps({
    "location_hash": location_hash,
    "zkp_proof": zkp_proof_serializable,
    "purpose": purpose
}).encode('utf-8')
encrypted_data = self.key_management.encrypt(combined_data)
```

- **Combined Data**:
  - Includes the `location_hash`, serialized `zkp_proof`, and the specified `purpose`.
  - Serialized to JSON and encoded to bytes for encryption.

- **Encryption**:
  - The `encrypt` method of `KeyManagement` encrypts the combined data.
  - Ensures that sensitive information is secured and only accessible to authorized parties.

### **7. Address Creation**

```python
encoded_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
address_hash = blake3.blake3(encoded_data.encode('utf-8')).hexdigest()
address_prefix = "AXM"
address = f"{address_prefix}_{address_hash}"
```

- **Base64 Encoding**:
  - Converts the encrypted data into a text format suitable for inclusion in URLs or storage.
  - `urlsafe_b64encode` ensures that the encoded data doesn't include characters that need to be escaped in URLs.

- **Final Address Hash**:
  - Hashing the Base64-encoded data produces a unique and consistent address hash.
  - Blake3 is used again for its cryptographic properties.

- **Address Prefix**:
  - A predefined prefix (e.g., "AXM") is added to the address to indicate its type or system.
  - Helps in differentiating addresses within different contexts or systems.

- **Complete Address**:
  - The final address is a combination of the prefix and the address hash, separated by an underscore.
  - Example format: `"AXM_123abc..."`

---

## **Exception Handling**

The method includes exception handling to capture and log any errors that occur during the address generation process.

```python
except Exception as e:
    logger.error(f"Error generating geohashed address: {e}", exc_info=True)
    raise
```

- **Logging**:
  - Errors are logged with detailed traceback information (`exc_info=True`).
  - Helps in debugging and identifying issues during execution.

- **Raising Exceptions**:
  - Exceptions are re-raised after logging to ensure that calling functions are aware of the failure.

---

## **Usage Example**

```python
if __name__ == "__main__":
    manager = AddressManager()
    try:
        address = manager.generate_geohashed_address("8.8.8.8", "wallet")
        print(f"Generated Address: {address}")
    except Exception as e:
        print(f"Failed to generate address: {e}")
```

- **Generating an Address**:
  - Instantiate the `AddressManager`.
  - Call `generate_geohashed_address` with an IP address and a purpose (e.g., "wallet").

- **Output**:
  - Prints the generated address or an error message if the process fails.

---

## **Dependencies and Requirements**

- **GeoIP Database**:
  - The `GeoLite2-City.mmdb` file must be available at the specified path.
  - Obtainable from MaxMind's website, subject to their licensing agreement.

- **External Libraries**:
  - `blake3`: For hashing functions.
  - `geoip2`: For GeoIP data retrieval.
  - `numpy`: For numerical operations and vector handling.
  - `base64`: For encoding binary data to text.

- **Custom Modules**:
  - `QuantumZKP`: A class handling zero-knowledge proof generation.
  - `KeyManagement`: Manages encryption keys and provides encryption functionality.

---

## **Security Considerations**

- **Data Privacy**:
  - Actual location data is never exposed directly; it's hashed and included in a ZKP.
  - Encryption ensures that sensitive data is protected during storage and transmission.

- **Zero-Knowledge Proofs**:
  - Allows validation of knowledge without revealing the underlying data.
  - Enhances privacy and security by minimizing data exposure.

- **Hashing Functions**:
  - Blake3 provides strong cryptographic hashing, preventing reverse-engineering of data from the hash.

---

## **Potential Use Cases**

- **Wallet Addresses**:
  - Generating addresses for cryptocurrency wallets with embedded location verification.

- **Access Control**:
  - Creating location-bound addresses or tokens for access to services or resources.

- **Identity Verification**:
  - Associating addresses with geolocation data for fraud prevention or compliance purposes.

---

## **Extensibility**

- **Purpose Differentiation**:
  - The `purpose` parameter allows the same process to generate addresses for different use cases.
  - Can be extended to include more context or metadata as needed.

- **Adaptable Dimensions**:
  - The `QuantumZKP` class is configured with a dimension parameter, allowing for adjustments based on security requirements.

- **Modular Components**:
  - The use of separate classes for key management and ZKP allows for easy replacement or enhancement of these components.

---

## **Conclusion**

The `AddressManager` class provides a comprehensive approach to generating secure, geohashed addresses that incorporate advanced cryptographic techniques. By combining GeoIP data, zero-knowledge proofs, encryption, and hashing, it ensures that addresses are unique, verifiable, and secure, while maintaining data privacy.

