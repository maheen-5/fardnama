"""Tests for the forensics pipeline step (Section 5).

Two kinds of test here, on purpose:
  - real synthetic images, for the behaviour a reviewer sees (a recompressed copy is linked,
    an unrelated picture is not, a PNG gets no ELA);
  - constructed hashes with a known number of flipped bits, for the threshold and ordering
    logic, so those assertions do not depend on how Pillow happens to render a test image.

Images are generated in memory. No real evidence is used.
"""
import io

import pytest
from PIL import Image, ImageDraw

from app.models.ledger import compute_entry_hash
from app.services.custody_payload import canonical_json, output_hash, output_hash_hex
from app.services.forensics_pipeline import (
    CUSTODY_STAGE, SCHEMA_VERSION, analyse_image, custody_output_hash, ela_panel_png,
)
from app.services.hashing import sha256_bytes
from app.services.phash import phash_bytes


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
    d.rectangle([0, 350, 270, 480], fill=(60, 130, 60))
    return img


def to_bytes(img: Image.Image, fmt: str = "PNG", **kw) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def flip_bits(hex_hash: str, count: int) -> str:
    """Return a hash that differs from hex_hash in exactly `count` bits."""
    value = int(hex_hash, 16)
    for bit in range(count):
        value ^= 1 << bit
    return f"{value:0{len(hex_hash)}x}"


PNG_CHAT = to_bytes(chat_like())
JPEG_CHAT = to_bytes(chat_like(), "JPEG", quality=90)
OWN_HASH_256 = phash_bytes(JPEG_CHAT)

EXPECTED_KEYS = {
    "schema_version", "image_sha256", "input_format", "phash", "similar_evidence",
    "ela", "ela_panel_ref", "notes", "created_at", "disclaimer",
}


# ---- the agreed result shape (docs/interfaces.md section 2) ----

def test_result_has_exactly_the_agreed_keys():
    result = analyse_image(JPEG_CHAT)
    assert set(result) == EXPECTED_KEYS
    assert result["schema_version"] == SCHEMA_VERSION
    assert set(result["phash"]) == {"value", "hash_bits"}
    assert result["phash"]["hash_bits"] == 256
    assert len(result["phash"]["value"]) == 64
    assert result["ela_panel_ref"] is None          # the pipeline fills this after storing
    assert "do not prove" in result["disclaimer"]
    assert result["created_at"].endswith("Z")


def test_image_sha256_is_the_hash_of_the_analysed_bytes():
    """The result must be tied to the exact bytes analysed, for the custody chain."""
    assert analyse_image(JPEG_CHAT)["image_sha256"] == sha256_bytes(JPEG_CHAT)


def test_jpeg_gets_ela_numbers():
    ela = analyse_image(JPEG_CHAT)["ela"]
    assert ela is not None
    assert set(ela) == {"quality", "mean_error", "p99_error", "max_error", "block_size",
                        "brightest_blocks", "note"}
    assert ela["quality"] == 90 and ela["block_size"] == 16
    assert 0 <= ela["mean_error"] <= ela["p99_error"] <= ela["max_error"] <= 255
    assert len(ela["brightest_blocks"]) == 5


def test_png_gets_no_ela_and_says_why():
    """A lossless image has no compression history, so ELA numbers would mislead."""
    result = analyse_image(PNG_CHAT)
    assert result["input_format"] == "PNG"
    assert result["ela"] is None
    assert any("lossless" in note for note in result["notes"])


def test_quality_argument_reaches_the_ela_result():
    assert analyse_image(JPEG_CHAT, quality=95)["ela"]["quality"] == 95


def test_hash_size_argument_is_respected():
    result = analyse_image(JPEG_CHAT, hash_size=8)
    assert result["phash"]["hash_bits"] == 64 and len(result["phash"]["value"]) == 16


# ---- duplicate detection inside one case ----

def test_no_case_history_gives_an_empty_list():
    assert analyse_image(JPEG_CHAT)["similar_evidence"] == []


def test_recompressed_copy_of_case_evidence_is_linked():
    """SHA-256 differs after a re-encode, so only pHash can recognise the same screenshot."""
    stored = [{"evidence_id": "ev_0001", "phash": phash_bytes(PNG_CHAT)}]
    result = analyse_image(JPEG_CHAT, stored)
    assert sha256_bytes(JPEG_CHAT) != sha256_bytes(PNG_CHAT)
    assert len(result["similar_evidence"]) == 1
    match = result["similar_evidence"][0]
    assert match["evidence_id"] == "ev_0001"
    assert match["verdict"] == "near_duplicate"


def test_unrelated_case_evidence_is_left_out():
    stored = [{"evidence_id": "ev_0002", "phash": phash_bytes(to_bytes(landscape()))}]
    assert analyse_image(JPEG_CHAT, stored)["similar_evidence"] == []


def test_verdict_bands_and_exclusion_of_different():
    """3/256 bits = near_duplicate, 40/256 = possibly_related, 100/256 = different (dropped)."""
    stored = [
        {"evidence_id": "ev_near", "phash": flip_bits(OWN_HASH_256, 3)},
        {"evidence_id": "ev_related", "phash": flip_bits(OWN_HASH_256, 40)},
        {"evidence_id": "ev_different", "phash": flip_bits(OWN_HASH_256, 100)},
    ]
    similar = analyse_image(JPEG_CHAT, stored)["similar_evidence"]
    assert [m["evidence_id"] for m in similar] == ["ev_near", "ev_related"]
    assert similar[0]["verdict"] == "near_duplicate"
    assert similar[1]["verdict"] == "possibly_related"


def test_similar_evidence_is_sorted_most_similar_first():
    stored = [
        {"evidence_id": "ev_far", "phash": flip_bits(OWN_HASH_256, 40)},
        {"evidence_id": "ev_exact", "phash": OWN_HASH_256},
        {"evidence_id": "ev_close", "phash": flip_bits(OWN_HASH_256, 5)},
    ]
    similar = analyse_image(JPEG_CHAT, stored)["similar_evidence"]
    assert [m["distance"] for m in similar] == [0, 5, 40]


# ---- one bad stored row must not stop new evidence being preserved ----

def test_different_hash_size_in_history_is_noted_not_compared():
    stored = [{"evidence_id": "ev_old", "phash": phash_bytes(JPEG_CHAT, hash_size=8)}]
    result = analyse_image(JPEG_CHAT, stored)
    assert result["similar_evidence"] == []
    assert any("different pHash size" in note for note in result["notes"])


def test_unreadable_stored_hash_is_noted_not_raised():
    stored = [{"evidence_id": "ev_bad", "phash": "z" * len(OWN_HASH_256)}]
    result = analyse_image(JPEG_CHAT, stored)
    assert result["similar_evidence"] == []
    assert any("unreadable" in note for note in result["notes"])


def test_incomplete_stored_entry_is_noted_not_raised():
    result = analyse_image(JPEG_CHAT, [{"evidence_id": "ev_x"}, {}])
    assert result["similar_evidence"] == []
    assert len(result["notes"]) == 2


# ---- bad input ----

@pytest.mark.parametrize("bad", [b"not an image", b"", "a string", None])
def test_invalid_input_raises_value_error(bad):
    """The API maps ValueError to HTTP 400, as the existing endpoints already do."""
    with pytest.raises(ValueError):
        analyse_image(bad)


# ---- the ELA panel, returned separately so the result stays pure JSON ----

def test_ela_panel_png_is_a_three_panel_png():
    png = ela_panel_png(JPEG_CHAT)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(io.BytesIO(png)) as panel:
        assert panel.width == 3 * 270


# ---- custody event: the result must hash into the ledger ----

def test_custody_output_hash_is_accepted_by_the_ledger():
    """End to end: result -> canonical JSON -> 32 bytes -> a FORENSICS custody entry."""
    digest = custody_output_hash(analyse_image(JPEG_CHAT))
    assert isinstance(digest, bytes) and len(digest) == 32
    entry = compute_entry_hash(bytes(32), CUSTODY_STAGE, digest, 1762000000000)
    assert len(entry) == 32


def test_canonical_json_ignores_key_order():
    """A verifier recomputing the hash must not depend on dict insertion order."""
    a = {"b": 2, "a": 1, "c": [3, {"y": 1, "x": 2}]}
    b = {"c": [3, {"x": 2, "y": 1}], "a": 1, "b": 2}
    assert canonical_json(a) == canonical_json(b)
    assert output_hash(a) == output_hash(b)


def test_canonical_json_has_no_whitespace_and_keeps_urdu_as_is():
    encoded = canonical_json({"text": "تم کہاں ہو", "n": 1})
    assert b", " not in encoded and b": " not in encoded
    assert "تم کہاں ہو".encode("utf-8") in encoded     # not \u-escaped


def test_output_hash_changes_when_any_value_changes():
    base = {"verdict": "near_duplicate", "distance": 2}
    changed = {"verdict": "near_duplicate", "distance": 3}
    assert output_hash(base) != output_hash(changed)
    assert output_hash_hex(base) == output_hash(base).hex()
