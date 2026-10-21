"""Cryptographic hashing helpers used to preserve evidence integrity."""
from hashlib import sha256


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hexadecimal SHA-256 digest of bytes."""
    if not isinstance(data, bytes):
        raise TypeError("sha256_bytes expects bytes")
    return sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """Hash a file in chunks, avoiding loading large files into memory."""
    digest = sha256()
    with open(path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
