
"""Tests for the evidence upload endpoint."""

import io
from hashlib import sha256

from fastapi.testclient import TestClient
from PIL import Image

from app.api import evidence as evidence_api
from app.main import app

client = TestClient(app)


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={
            "file": (
                "payload.exe",
                b"not an allowed type",
                "application/octet-stream",
            )
        },
    )
    assert response.status_code == 415


def test_upload_requires_consent():
    response = client.post(
        "/api/evidence/upload",
        data={"consent": "false"},
        files={"file": ("note.txt", b"sample text", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_image_returns_hash_and_ocr_status(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        evidence_api,
        "extract_text_from_image_bytes",
        lambda data: "hello evidence",
    )

    image = Image.new("RGB", (100, 40), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    raw = buffer.getvalue()

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("sample.png", raw, "image/png")},
    )
    assert response.status_code == 201

    body = response.json()
    assert len(body["sha256"]) == 64
    assert body["extracted_text"] == "hello evidence"
    assert body["ocr_status"] == "completed"

    saved = tmp_path / f'{body["evidence_id"]}.png'
    assert saved.read_bytes() == raw


def _png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 40), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_corrupt_image_returns_400(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("broken.png", b"this is not a png", "image/png")},
    )
    assert response.status_code == 400
    assert "decoded" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []


def test_upload_empty_file_returns_400(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_oversize_file_returns_413(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(evidence_api, "MAX_UPLOAD_BYTES", 10)

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("big.txt", b"x" * 11, "text/plain")},
    )
    assert response.status_code == 413


def test_upload_text_file_is_hashed_and_stored_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)
    raw = b"a plain text evidence note"

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("note.txt", raw, "text/plain")},
    )
    assert response.status_code == 201

    body = response.json()
    assert body["sha256"] == sha256(raw).hexdigest()
    assert body["ocr_status"] == "not_applicable"
    assert (tmp_path / f'{body["evidence_id"]}.txt').read_bytes() == raw


def test_missing_tesseract_is_503_not_a_decode_error(tmp_path, monkeypatch):
    """A valid PNG must not be reported as undecodable when Tesseract is missing."""
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setenv("TESSERACT_CMD", "/definitely/not/here/tesseract")

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("valid.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 503
    assert "Tesseract" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_too_many_pixels(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_api, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(evidence_api, "MAX_IMAGE_PIXELS", 100)
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")

    response = client.post(
        "/api/evidence/upload",
        data={"consent": "true"},
        files={"file": ("bomb.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Image exceeds the pixel limit"
    assert list(tmp_path.iterdir()) == []
