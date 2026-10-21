"""Mid-1 prototype of ADR-001 section 5; not persisted, not anchored."""

from dataclasses import dataclass
from hashlib import sha256

_ALLOWED_STAGES = {
    "INGEST",
    "COPY",
    "STORE",
    "OCR",
    "FORENSICS",
    "CLASSIFY",
}
_ZERO_HASH = bytes(32)


@dataclass
class CustodyEvent:
    """One ordered processing event for an evidence item."""

    evidence_id: str
    stage: str
    output_hash: str
    timestamp_ms: int
    prev_entry_hash: str
    entry_hash: str
    case_seq: int


def compute_entry_hash(
    prev_entry_hash: bytes,
    stage: str,
    output_hash: bytes,
    ts_ms: int,
) -> bytes:
    """Hash an event using the ADR-001 section 5 encoding."""
    if stage not in _ALLOWED_STAGES:
        raise ValueError(f"Unsupported custody stage: {stage}")
    try:
        stage_bytes = stage.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("stage must contain only ASCII characters") from exc
    if len(stage_bytes) > 255:
        raise ValueError("stage is too long")
    if len(prev_entry_hash) != 32:
        raise ValueError("prev_entry_hash must be 32 bytes")
    if len(output_hash) != 32:
        raise ValueError("output_hash must be 32 bytes")
    if not 0 <= ts_ms < 2**64:
        raise ValueError("ts_ms must fit in an unsigned 8-byte integer")

    encoded = (
        prev_entry_hash
        + len(stage_bytes).to_bytes(1, "big")
        + stage_bytes
        + output_hash
        + ts_ms.to_bytes(8, "big")
    )
    return sha256(encoded).digest()


def verify_chain(events: list[CustodyEvent]) -> bool:
    """Verify genesis, event hashes, and previous-hash links in order."""
    previous = _ZERO_HASH
    previous_seq = None
    for event in events:
        try:
            prev_hash = bytes.fromhex(event.prev_entry_hash)
            output_hash = bytes.fromhex(event.output_hash)
            entry_hash = bytes.fromhex(event.entry_hash)
            calculated_hash = compute_entry_hash(
                prev_hash,
                event.stage,
                output_hash,
                event.timestamp_ms,
            )
        except (TypeError, ValueError, AttributeError):
            return False

        if (
            (previous_seq is not None and event.case_seq <= previous_seq)
            or prev_hash != previous
            or entry_hash != calculated_hash
        ):
            return False
        previous = entry_hash
        previous_seq = event.case_seq
    return True
