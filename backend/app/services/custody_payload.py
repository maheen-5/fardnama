"""Canonical encoding of a pipeline result for the custody ledger.

Why this module exists
  app/models/ledger.py's compute_entry_hash() needs a 32-byte output_hash for every custody
  event. Three pipeline stages produce a JSON result rather than raw bytes: forensics
  (Section 5), classification (Sections 6 and 7) and the SLM summary (Section 15). They
  therefore need ONE agreed way to turn that JSON into those 32 bytes, so the same result
  always hashes to the same value and a verifier can recompute it later from the stored
  result alone.

The rule (docs/interfaces.md, section 0.4)
  output_hash = SHA-256 of the result's canonical JSON:
  keys sorted, separators (",", ":"), UTF-8, no extra whitespace.

Two deliberate choices
  - ensure_ascii=False: evidence text is Urdu and Roman Urdu. Escaping non-ASCII characters
    would make the hashed bytes depend on the escaping style rather than on the content.
  - sort_keys=True: a dict with the same contents in a different insertion order must hash
    to the same value, otherwise a verifier recomputing the hash could fail for no reason.

This module is owned by Sections 5/6/7/15 and is only READ by the ledger (Section 2).
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Mapping


def canonical_json(result: Mapping) -> bytes:
    """Return the canonical JSON bytes of a result object.

    Raises TypeError if the result holds a value JSON cannot represent, which is deliberate:
    a result that cannot be encoded must not silently get a hash over a partial payload.
    """
    return json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def output_hash(result: Mapping) -> bytes:
    """32-byte SHA-256 digest of the canonical JSON, ready for compute_entry_hash()."""
    return sha256(canonical_json(result)).digest()


def output_hash_hex(result: Mapping) -> str:
    """Same digest as output_hash(), as a 64-character hex string for storage and logs."""
    return sha256(canonical_json(result)).hexdigest()
