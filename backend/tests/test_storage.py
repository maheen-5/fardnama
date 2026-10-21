"""Tests for the local evidence storage backend."""

from uuid import uuid4

import pytest

from app.services.hashing import sha256_bytes
from app.services.storage import LocalStorage


def test_local_storage_round_trip(tmp_path):
    storage = LocalStorage(tmp_path)
    data = b"original evidence bytes"

    ref = storage.save(str(uuid4()), ".txt", data)

    assert storage.exists(ref)
    assert storage.load(ref) == data


def test_verify_stored_detects_tampering(tmp_path):
    storage = LocalStorage(tmp_path)
    data = b"original evidence bytes"
    ref = storage.save(str(uuid4()), ".txt", data)

    assert storage.verify_stored(ref, sha256_bytes(data))
    (tmp_path / ref).write_bytes(b"modified evidence bytes")
    assert not storage.verify_stored(ref, sha256_bytes(data))


def test_local_storage_refuses_to_overwrite(tmp_path):
    storage = LocalStorage(tmp_path)
    evidence_id = str(uuid4())
    storage.save(evidence_id, ".txt", b"first")

    with pytest.raises(FileExistsError):
        storage.save(evidence_id, ".txt", b"second")


def test_local_storage_rejects_path_traversal_id(tmp_path):
    storage = LocalStorage(tmp_path)

    with pytest.raises(ValueError, match="UUID"):
        storage.save("../x", ".txt", b"evidence")
