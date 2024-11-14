def rle_encode(data: bytes) -> bytes:
    """Run-Length Encode a sequence of bytes."""
    encoded = bytearray()
    i = 0
    while i < len(data):
        count = 1
        while i + 1 < len(data) and data[i] == data[i + 1] and count < 255:
            count += 1
            i += 1
        encoded.extend([data[i], count])
        i += 1
    return bytes(encoded)

def rle_decode(data: bytes) -> bytes:
    """Decode a Run-Length Encoded sequence of bytes."""
    decoded = bytearray()
    i = 0
    while i < len(data):
        value = data[i]
        count = data[i + 1]
        decoded.extend([value] * count)
        i += 2
    return bytes(decoded)
