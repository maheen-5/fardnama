"""Forensics step of the evidence pipeline (Section 5).

What this adds on top of the Mid-1 prototype
  app/services/phash.py and app/services/ela.py are pure single-image functions, and
  app/api/forensics.py exposes them as four stand-alone endpoints that store nothing and
  know nothing about cases. This module is the step the UPLOAD PIPELINE calls instead: it
  runs both techniques on the working copy of one evidence item, compares that item with the
  evidence already held in the SAME case, and returns one result object in the shape agreed
  in docs/interfaces.md, section 2.

Boundaries, on purpose
  - Stores nothing; opens no file, socket or database. The pipeline (Section 1) stores the
    result, stores the ELA panel through the storage service (Section 4), and appends the
    custody event through the ledger (Section 2). Keeping this function pure is what lets it
    be tested without the rest of the application, as the Mid-1 prototype already is.
  - Runs on the WORKING COPY, never the original. The original is hashed at ingestion and
    left untouched (FR3); the caller is responsible for passing the copy's bytes.
  - Duplicate detection is scoped to one case. The caller passes only that case's hashes, so
    no hash is ever compared across two cases (NFR8, case isolation).
  - The result is an INDICATOR for a human reviewer, never a finding. pHash reports visual
    similarity and says nothing about editing; ELA points at regions worth a closer look.
    The disclaimer travels with the result so that a screen or report cannot drop it.

Known cost
  If the caller also wants the three-panel picture it calls ela_panel_png(), which runs the
  ELA computation a second time. That is accepted at FYP-1 scale in exchange for keeping one
  source of truth in ela.py; if upload latency becomes a problem under NFR4 the two calls can
  be merged into one pass later.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Optional, Sequence

from app.services.custody_payload import output_hash
from app.services.ela import DEFAULT_QUALITY, analyse, analyse_to_png
from app.services.hashing import sha256_bytes
from app.services.phash import DEFAULT_HASH_SIZE, compare_hashes, phash_bytes

SCHEMA_VERSION = "1.0"

# Stage name for the custody event this result belongs to. Already accepted by
# app/models/ledger.py's _ALLOWED_STAGES, so the pipeline should not hardcode the string.
CUSTODY_STAGE = "FORENSICS"

DISCLAIMER = (
    "Forensic indicators for a human reviewer; "
    "they do not prove or rule out manipulation."
)


def _utc_now_iso() -> str:
    """Current time as ISO 8601 in UTC with a Z suffix, to the second."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _as_bytes(image_bytes: bytes) -> bytes:
    """Accept bytes or bytearray; reject anything else with the same error as phash/ela."""
    if isinstance(image_bytes, bytes):
        return image_bytes
    if isinstance(image_bytes, bytearray):
        return bytes(image_bytes)
    raise ValueError("Expected non-empty image bytes.")


def _compare_with_case(
    own_hash: str,
    case_phashes: Sequence[Mapping[str, str]],
    notes: list,
) -> list:
    """Compare this item's pHash with the other items in the same case.

    Only near_duplicate and possibly_related are reported; items judged different are left
    out, so an empty list means nothing in the case resembles this item. A stored hash that
    cannot be compared is skipped and noted rather than failing the whole upload: one bad
    historical row must not stop new evidence from being preserved.
    """
    similar = []
    for entry in case_phashes:
        evidence_id = entry.get("evidence_id") if hasattr(entry, "get") else None
        other_hash = entry.get("phash") if hasattr(entry, "get") else None
        if not evidence_id or not other_hash:
            notes.append("A stored case entry had no evidence_id or pHash and was skipped.")
            continue
        if len(other_hash) != len(own_hash):
            notes.append(
                f"Evidence {evidence_id} was hashed at a different pHash size "
                "and was not compared."
            )
            continue
        try:
            comparison = compare_hashes(own_hash, other_hash)
        except ValueError:
            notes.append(
                f"Evidence {evidence_id} has an unreadable stored pHash and was not compared."
            )
            continue
        if comparison.verdict == "different":
            continue
        similar.append(
            {
                "evidence_id": evidence_id,
                "distance": comparison.distance,
                "distance_fraction": comparison.distance_fraction,
                "verdict": comparison.verdict,
            }
        )
    # Most similar first; evidence_id breaks ties so the order is deterministic in tests
    # and in the report.
    similar.sort(key=lambda item: (item["distance"], item["evidence_id"]))
    return similar


def analyse_image(
    image_bytes: bytes,
    case_phashes: Sequence[Mapping[str, str]] = (),
    *,
    hash_size: int = DEFAULT_HASH_SIZE,
    quality: int = DEFAULT_QUALITY,
) -> dict:
    """Run pHash and ELA on one working copy and report it against the rest of the case.

    Args:
        image_bytes: the working copy of the evidence image. Never the original.
        case_phashes: the other evidence in the SAME case, as
            [{"evidence_id": str, "phash": str}]. Supplied by the pipeline from stored
            results; an empty sequence means this is the first image in the case.
        hash_size: pHash size; 16 gives the 256-bit default chosen in Mid-1.
        quality: JPEG quality used for the ELA re-save.

    Returns:
        The result object described in docs/interfaces.md section 2. ela_panel_ref is left
        None for the pipeline to fill once it has stored the panel.

    Raises:
        ValueError: the bytes are empty or are not a readable image. The caller maps this to
            HTTP 400, as the existing endpoints already do.
    """
    data = _as_bytes(image_bytes)

    own_hash = phash_bytes(data, hash_size)
    ela_result, _original, _ela_image, _heatmap = analyse(data, quality=quality)

    notes: list = []
    similar_evidence = _compare_with_case(own_hash, case_phashes, notes)

    if ela_result.input_format == "JPEG":
        ela_payload: Optional[dict] = {
            "quality": ela_result.quality,
            "mean_error": ela_result.mean_error,
            "p99_error": ela_result.p99_error,
            "max_error": ela_result.max_error,
            "block_size": ela_result.block_size,
            "brightest_blocks": ela_result.brightest_blocks,
            "note": ela_result.note,
        }
    else:
        # A lossless image has no compression history, so ELA numbers would describe edges
        # and colour rather than edits. Reporting them as ELA would invite a wrong reading.
        ela_payload = None
        notes.append(
            f"{ela_result.input_format} is lossless: ELA is not applicable here and would "
            "show edges only, so no ELA result is reported."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "image_sha256": sha256_bytes(data),
        "input_format": ela_result.input_format,
        "phash": {"value": own_hash, "hash_bits": len(own_hash) * 4},
        "similar_evidence": similar_evidence,
        "ela": ela_payload,
        "ela_panel_ref": None,
        "notes": notes,
        "created_at": _utc_now_iso(),
        "disclaimer": DISCLAIMER,
    }


def ela_panel_png(image_bytes: bytes, *, quality: int = DEFAULT_QUALITY) -> bytes:
    """The three-panel ELA picture (original | ELA | heatmap) as PNG bytes.

    Returned separately from analyse_image() so that the result object stays pure JSON: the
    pipeline stores these bytes through the storage service and writes the reference into
    the result's ela_panel_ref field.
    """
    return analyse_to_png(_as_bytes(image_bytes), quality=quality)


def custody_output_hash(result: Mapping) -> bytes:
    """32-byte output_hash for this result's FORENSICS custody event.

    Re-exported here so the pipeline has one import for the forensics stage and does not
    need to know how the canonical encoding is defined.
    """
    return output_hash(result)
