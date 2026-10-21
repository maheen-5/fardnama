"""Tests for the pHash prototype (service + API).

Images are generated in memory: no real evidence.
"""
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageEnhance

from app.api.forensics import router as forensics_router
from app.services.phash import (
    compare_hashes, compare_images, hamming_distance, phash_bytes, verdict_for,
)


def chat_like(seed: int = 0) -> Image.Image:
    """A small synthetic 'screenshot' with a header and message bubbles."""
    img = Image.new("RGB", (270, 480), (236, 229, 221))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 270, 45], fill=(18, 140, 126))
    for i in range(6):
        y = 60 + i * 60
        left = (i + seed) % 2 == 0
        x0, x1 = (10, 180) if left else (90, 260)
        d.rounded_rectangle([x0, y, x1, y + 40], radius=8,
                            fill=(255, 255, 255) if left else (220, 248, 198))
        d.text((x0 + 8, y + 12), f"message {i + seed}", fill="black")
    return img


def landscape() -> Image.Image:
    img = Image.new("RGB", (270, 480))
    d = ImageDraw.Draw(img)
    for y in range(480):
        d.line([(0, y), (270, y)], fill=(int(40 + 200 * y / 480), 120, int(200 - 150 * y / 480)))
    d.ellipse([170, 60, 235, 125], fill=(255, 220, 90))
    d.polygon([(0, 350), (90, 210), (180, 350)], fill=(70, 90, 70))
    d.rectangle([0, 350, 270, 480], fill=(60, 130, 60))
    return img


def to_bytes(img: Image.Image, fmt: str = "PNG", **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


ORIGINAL = to_bytes(chat_like())


def test_hash_format_and_determinism():
    h = phash_bytes(ORIGINAL)
    assert h == phash_bytes(ORIGINAL)
    assert len(h) == 64 and int(h, 16) >= 0          # 256 bits by default
    assert len(phash_bytes(ORIGINAL, hash_size=8)) == 16


def test_identical_image_distance_zero():
    r = compare_images(ORIGINAL, ORIGINAL)
    assert r.distance == 0 and r.similarity == 1.0 and r.verdict == "near_duplicate"


@pytest.mark.parametrize("variant", [
    to_bytes(chat_like().resize((135, 240))),            # resized copy
    to_bytes(chat_like(), "JPEG", quality=60),           # recompressed copy (e.g. forwarded)
])
def test_resaved_copies_are_near_duplicates_even_though_sha256_changes(variant):
    from app.services.hashing import sha256_bytes
    assert sha256_bytes(variant) != sha256_bytes(ORIGINAL)
    assert compare_images(ORIGINAL, variant).verdict == "near_duplicate"


def test_unrelated_image_is_different():
    r = compare_images(ORIGINAL, to_bytes(landscape()))
    assert r.verdict == "different"
    assert r.distance_fraction > 0.25


def test_brightness_change_moves_hash_less_than_unrelated_image():
    bright = to_bytes(ImageEnhance.Brightness(chat_like()).enhance(1.2))
    unrelated = to_bytes(landscape())
    assert compare_images(ORIGINAL, bright).distance < compare_images(ORIGINAL, unrelated).distance


def test_hamming_distance_and_verdict_rules():
    assert hamming_distance("ff", "00") == 8
    assert hamming_distance("0f", "0e") == 1
    with pytest.raises(ValueError):
        hamming_distance("ff", "fff")
    assert verdict_for(0.10) == "near_duplicate"
    assert verdict_for(0.20) == "possibly_related"
    assert verdict_for(0.30) == "different"
    assert compare_hashes("ff", "00").verdict == "different"


def test_invalid_image_bytes_raise_value_error():
    with pytest.raises(ValueError):
        phash_bytes(b"not an image")
    with pytest.raises(ValueError):
        phash_bytes(b"")


# ---- API (mounted on a test app, so this test does not depend on app/main.py) ----
api = FastAPI()
api.include_router(forensics_router, prefix="/api")
client = TestClient(api)


def test_api_compare_returns_similarity_and_sha256_flag():
    copy = to_bytes(chat_like(), "JPEG", quality=60)
    resp = client.post(
        "/api/forensics/phash/compare",
        data={
            "consent": "true"},
        files={
            "file_a": (
                "original.png",
                ORIGINAL,
                "image/png"),
            "file_b": (
                "copy.jpg",
                copy,
                "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sha256_identical"] is False
    assert body["verdict"] == "near_duplicate"
    assert body["hash_bits"] == 256


def test_api_requires_consent():
    resp = client.post(
        "/api/forensics/phash/compare",
        data={
            "consent": "false"},
        files={
            "file_a": (
                "a.png",
                ORIGINAL,
                "image/png"),
            "file_b": (
                "b.png",
                ORIGINAL,
                "image/png")},
    )
    assert resp.status_code == 400


def test_api_rejects_non_image_and_undecodable_image():
    resp = client.post("/api/forensics/phash", data={"consent": "true"},
                       files={"file": ("notes.txt", b"hello", "text/plain")})
    assert resp.status_code == 415
    resp = client.post("/api/forensics/phash", data={"consent": "true"},
                       files={"file": ("broken.png", b"not really a png", "image/png")})
    assert resp.status_code == 400


def test_api_single_hash_supports_64_bit():
    resp = client.post("/api/forensics/phash?hash_size=8", data={"consent": "true"},
                       files={"file": ("a.png", ORIGINAL, "image/png")})
    assert resp.status_code == 200
    assert resp.json()["hash_bits"] == 64 and len(resp.json()["phash"]) == 16
