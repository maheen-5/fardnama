"""Tests for custody-event hashing and chain verification."""

from dataclasses import replace
from hashlib import sha256

import pytest

from app.models import CustodyEvent, compute_entry_hash, verify_chain


def _build_chain():
    output_hash = sha256(b"original").digest()
    genesis_prev_hash = bytes(32)
    genesis_hash = compute_entry_hash(
        genesis_prev_hash,
        "INGEST",
        output_hash,
        1000,
    )
    first = CustodyEvent(
        evidence_id="evidence-id",
        stage="INGEST",
        output_hash=output_hash.hex(),
        timestamp_ms=1000,
        prev_entry_hash=genesis_prev_hash.hex(),
        entry_hash=genesis_hash.hex(),
        case_seq=1,
    )

    second_output_hash = sha256(b"copy").digest()
    second_hash = compute_entry_hash(genesis_hash, "COPY", second_output_hash, 2000)
    second = CustodyEvent(
        evidence_id="evidence-id",
        stage="COPY",
        output_hash=second_output_hash.hex(),
        timestamp_ms=2000,
        prev_entry_hash=genesis_hash.hex(),
        entry_hash=second_hash.hex(),
        case_seq=2,
    )
    return [first, second]


def test_custody_chain_detects_modified_entry():
    events = _build_chain()

    assert verify_chain(events)
    assert not verify_chain([events[0], replace(events[1], stage="STORE")])
    assert not verify_chain(
        [events[0], replace(events[1], output_hash=sha256(b"tampered").hexdigest())]
    )
    assert not verify_chain([events[0], replace(events[1], timestamp_ms=3000)])


def test_custody_chain_genesis_uses_zero_prev():
    events = _build_chain()

    assert events[0].prev_entry_hash == bytes(32).hex()
    assert verify_chain(events)


def test_custody_chain_rejects_unknown_stage():
    with pytest.raises(ValueError, match="Unsupported custody stage"):
        compute_entry_hash(bytes(32), "UNKNOWN", bytes(32), 1000)
