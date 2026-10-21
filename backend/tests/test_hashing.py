from app.services.hashing import sha256_bytes


def test_sha256_hash_deterministic():
    payload = b"sample evidence bytes"
    assert sha256_bytes(payload) == sha256_bytes(payload)


def test_sha256_hash_changes_on_single_bit_flip():
    original = b"\x00"
    changed = b"\x01"
    assert sha256_bytes(original) != sha256_bytes(changed)
