import uuid
import hashlib

def generate_deterministic_id(*args) -> str:
    """Generates a UUID5 based on a SHA256 hash of the input arguments."""
    combined = "|".join(str(arg) for arg in args).encode('utf-8')
    hash_bytes = hashlib.sha256(combined).digest()
    # UUID5 requires a 16-byte hash. SHA256 is 32 bytes, we truncate it.
    return str(uuid.UUID(bytes=hash_bytes[:16], version=5))
