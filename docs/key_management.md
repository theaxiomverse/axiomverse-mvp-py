
# **AxiomVerse KeyManagement Class Documentation**

## **Overview**

The `KeyManagement` class is responsible for managing cryptographic keys and providing encryption and decryption functionalities. It utilizes:

- **Kyber-512**: A post-quantum cryptographic algorithm for key encapsulation.
- **AES-256**: Advanced Encryption Standard with a 256-bit key for symmetric encryption.

This class plays a crucial role in securely encrypting data within the address generation process, ensuring that sensitive information is protected from unauthorized access.

---

## **Class Structure**

```python
class KeyManagement:
    def __init__(self):
        self.key = os.urandom(32)  # 256-bit key for AES encryption
        self.kyber = Kyber512

    # Key Pair Generation
    def generate_keypair(self) -> Tuple[str, str]:
        ...

    # Key Encapsulation
    def encapsulate(self, public_key: str) -> Tuple[str, str]:
        ...

    # Key Decapsulation
    def decapsulate(self, secret_key: str, ciphertext: str) -> str:
        ...

    # Encryption
    def encrypt(self, plaintext: bytes) -> bytes:
        ...

    # Decryption
    def decrypt(self, encrypted_data) -> str:
        ...
```

---

## **Detailed Method Explanations**

### **1. Initialization**

```python
def __init__(self):
    self.key = os.urandom(32)  # 256-bit key for AES encryption
    self.kyber = Kyber512
```

- **Purpose**:
  - Initialize the key management system with a symmetric key for AES encryption and set up the Kyber-512 algorithm for public-key cryptography.
- **Components**:
  - `self.key`: A randomly generated 256-bit key used for AES encryption.
  - `self.kyber`: Reference to the Kyber-512 algorithm for key encapsulation mechanisms (KEM).

### **2. Key Pair Generation**

```python
def generate_keypair(self) -> Tuple[str, str]:
    pk, sk = self.kyber.keygen()
    return base64.b64encode(pk).decode(), base64.b64encode(sk).decode()
```

- **Purpose**:
  - Generate a public and private key pair using Kyber-512 for asymmetric cryptography.
- **Process**:
  - Calls `self.kyber.keygen()` to generate a key pair.
  - Encodes the public key (`pk`) and secret key (`sk`) using Base64 for safe storage or transmission.
- **Returns**:
  - A tuple containing the Base64-encoded public key and secret key as strings.

### **3. Key Encapsulation**

```python
def encapsulate(self, public_key: str) -> Tuple[str, str]:
    pk = base64.b64decode(public_key.encode())
    key, ciphertext = self.kyber.encaps(pk)
    return base64.b64encode(key).decode(), base64.b64encode(ciphertext).decode()
```

- **Purpose**:
  - Encapsulate a symmetric key using the recipient's public key, enabling secure key exchange.
- **Process**:
  - Decodes the recipient's public key from Base64.
  - Uses `self.kyber.encaps(pk)` to generate a shared symmetric key (`key`) and a ciphertext (`ciphertext`).
  - Encodes the symmetric key and ciphertext using Base64.
- **Returns**:
  - A tuple containing the Base64-encoded symmetric key and ciphertext.

### **4. Key Decapsulation**

```python
def decapsulate(self, secret_key: str, ciphertext: str) -> str:
    sk = base64.b64decode(secret_key.encode())
    ct = base64.b64decode(ciphertext.encode())
    key = self.kyber.decaps(sk, ct)
    return base64.b64encode(key).decode()
```

- **Purpose**:
  - Decapsulate the ciphertext using the recipient's secret key to retrieve the shared symmetric key.
- **Process**:
  - Decodes the secret key and ciphertext from Base64.
  - Uses `self.kyber.decaps(sk, ct)` to retrieve the shared symmetric key (`key`).
  - Encodes the symmetric key using Base64.
- **Returns**:
  - The Base64-encoded symmetric key as a string.

### **5. Encryption**

```python
def encrypt(self, plaintext: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_data = iv + ciphertext

    return encrypted_data
```

- **Purpose**:
  - Encrypt plaintext data using AES-256 in CBC mode.
- **Process**:
  - **Initialization Vector (IV)**:
    - Generates a random 16-byte IV for AES encryption.
  - **Cipher Setup**:
    - Creates a cipher object using AES-256 with the generated IV.
  - **Padding**:
    - Pads the plaintext using PKCS7 padding to ensure it fits the block size.
  - **Encryption**:
    - Encrypts the padded plaintext to produce the ciphertext.
  - **Combining IV and Ciphertext**:
    - Prepends the IV to the ciphertext for use during decryption.
- **Returns**:
  - The encrypted data as bytes, consisting of the IV followed by the ciphertext.

### **6. Decryption**

```python
def decrypt(self, encrypted_data) -> str:
    encrypted_data_bytes = base64.urlsafe_b64decode(encrypted_data)

    iv = encrypted_data_bytes[:16]
    ciphertext = encrypted_data_bytes[16:]

    cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext.decode('utf-8')
```

- **Purpose**:
  - Decrypt data that was encrypted using the `encrypt` method.
- **Process**:
  - **Decode Encrypted Data**:
    - Decodes the Base64-encoded encrypted data.
  - **Extract IV and Ciphertext**:
    - Separates the IV and the ciphertext from the encrypted data.
  - **Cipher Setup**:
    - Creates a cipher object using AES-256 with the extracted IV.
  - **Decryption**:
    - Decrypts the ciphertext to obtain the padded plaintext.
  - **Unpadding**:
    - Removes the PKCS7 padding to retrieve the original plaintext.
- **Returns**:
  - The decrypted plaintext as a UTF-8 encoded string.

---

## **Integration with Address Generation**

In the `AddressManager` class, the `KeyManagement` class is utilized to encrypt the combined data containing the location hash, ZKP proof, and purpose. This ensures that sensitive information is securely stored and transmitted.

### **Encryption in Address Generation**

```python
# In AddressManager.generate_geohashed_address

# Encrypt the location hash, ZKP proof, and purpose
combined_data = json.dumps({
    "location_hash": location_hash,
    "zkp_proof": zkp_proof_serializable,
    "purpose": purpose
}).encode('utf-8')
encrypted_data = self.key_management.encrypt(combined_data)
```

- **Process**:
  - The `combined_data` is serialized to JSON and encoded to bytes.
  - The `encrypt` method of `KeyManagement` is called to encrypt this data.
  - The encrypted data is then used to generate the final address.

### **Security Considerations**

- **Symmetric Key Security**:
  - The symmetric key used for AES encryption (`self.key`) is randomly generated during initialization and should be securely managed.
  - In a production environment, this key should be stored securely or derived using a secure method, rather than being generated each time the `KeyManagement` class is instantiated.

- **Asymmetric Key Exchange (Kyber-512)**:
  - The methods `generate_keypair`, `encapsulate`, and `decapsulate` provide functionality for secure key exchange using post-quantum cryptography.
  - While not directly used in the `AddressManager` code provided, these methods enable secure communication and key sharing between parties.

---

## **Example Usage**

### **Generating a Key Pair**

```python
key_mgmt = KeyManagement()
public_key, secret_key = key_mgmt.generate_keypair()
```

- **Purpose**:
  - Generate a public and secret key pair for use in key encapsulation.

### **Key Encapsulation and Decapsulation**

```python
# On the sender's side
symmetric_key, ciphertext = key_mgmt.encapsulate(public_key)

# On the receiver's side
derived_key = key_mgmt.decapsulate(secret_key, ciphertext)
```

- **Purpose**:
  - **Encapsulation**: The sender uses the receiver's public key to securely send a symmetric key.
  - **Decapsulation**: The receiver uses their secret key to retrieve the symmetric key.

### **Encryption and Decryption**

```python
# Encryption
plaintext = b"Sensitive data to encrypt"
encrypted_data = key_mgmt.encrypt(plaintext)

# Decryption
decrypted_text = key_mgmt.decrypt(base64.urlsafe_b64encode(encrypted_data))
```

- **Note**:
  - When decrypting, the encrypted data is Base64-encoded to match the expected input format of the `decrypt` method.

---

## **Important Notes**

### **1. Key Storage and Management**

- **Symmetric Key (`self.key`)**:
  - Currently generated using `os.urandom(32)` upon each instantiation.
  - **Recommendation**:
    - Persist the key securely across sessions if the same key needs to be used.
    - Consider using a key derivation function (KDF) if deriving keys from passwords or other secrets.

### **2. Security Practices**

- **Randomness**:
  - Ensure that `os.urandom` provides sufficient entropy on the operating system being used.
- **Padding Schemes**:
  - PKCS7 padding is used to align data with the AES block size.
- **Algorithm Choices**:
  - **AES-256**:
    - A widely accepted symmetric encryption standard.
  - **Kyber-512**:
    - A post-quantum algorithm, secure against quantum computer attacks.
    - **Note**: Ensure that the `kyber` library used is properly implemented and maintained.

### **3. Error Handling**

- The methods do not include explicit error handling.
- **Recommendation**:
  - Add try-except blocks to handle potential exceptions, such as invalid keys or data corruption.

---

## **Integration Considerations**

- **In Address Generation**:
  - The `encrypt` method is directly used to secure the combined data.
  - The `decrypt` method would be used wherever decryption of the data is required.
- **For Secure Communication**:
  - The key encapsulation and decapsulation methods can be used to securely share symmetric keys between parties, enabling encrypted communication.

---

## **Summary**

The `KeyManagement` class provides essential cryptographic functionalities that enhance the security of the address generation process. By leveraging both symmetric and asymmetric encryption methods, it ensures that sensitive data is protected during storage and transmission.

- **Symmetric Encryption (AES-256)**:
  - Used for encrypting data efficiently.
  - Suitable for encrypting large amounts of data.

- **Asymmetric Encryption (Kyber-512)**:
  - Facilitates secure key exchange.
  - Resistant to quantum attacks, future-proofing the cryptographic system.


---

## **Conclusion**

The integration of the `KeyManagement` class into the address generation process provides a robust security mechanism that protects sensitive information. It ensures that:

- Data is encrypted using strong cryptographic algorithms.
- Keys are managed securely.
- The system is resistant to both classical and quantum cryptographic attacks.
