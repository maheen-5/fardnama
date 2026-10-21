"""Tests for standard-library data models."""

from datetime import datetime, timezone

from app.models import Evidence


def test_evidence_to_dict_keys():
    evidence = Evidence(
        evidence_id="12345678-1234-5678-1234-567812345678",
        case_id=None,
        filename="evidence.txt",
        extension=".txt",
        size_bytes=8,
        sha256_original="a" * 64,
        sha256_copy=None,
        storage_ref="stored-ref",
        ocr_status="not_applicable",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert set(evidence.to_dict()) == {
        "evidence_id",
        "case_id",
        "filename",
        "extension",
        "size_bytes",
        "sha256_original",
        "sha256_copy",
        "storage_ref",
        "ocr_status",
        "created_at",
    }
