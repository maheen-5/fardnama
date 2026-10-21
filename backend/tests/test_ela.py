"""Tests for the ELA prototype (service + API). Images are generated in memory: no real evidence."""
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.api.forensics import router as forensics_router
from app.services.ela import analyse, analyse_to_png, error_level, load_rgb, region_mean

ROW_H = 40


def chat_rows(texts) -> Image.Image:
    """Simple synthetic chat: one text row per message."""
    img = Image.new("RGB", (320, ROW_H * len(texts)), (236, 229, 221))
    d = ImageDraw.Draw(img)
    for i, text in enumerate(texts):
        y = i * ROW_H
        d.rounded_rectangle([8, y + 4, 312, y + ROW_H - 4], radius=6, fill="white")
        d.text((16, y + 14), text, fill="black")
    return img


def jpeg_bytes(img: Image.Image, quality: int = 90) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


TEXTS = [f"message number {i} here" for i in range(8)]
EDITED = list(TEXTS)
EDITED[4] = "a different line of text"
BAND = (0, 4 * ROW_H, 320, 5 * ROW_H)


def received_and_edited():
    """Received JPEG (compressed once), unedited re-save, and an edit pasted in before re-saving."""
    received = load_rgb(jpeg_bytes(chat_rows(TEXTS)))[0]
    unedited = jpeg_bytes(received)
    edited_img = received.copy()
    edited_img.paste(chat_rows(EDITED).crop(BAND), BAND[:2])
    return unedited, jpeg_bytes(edited_img)


def edited_vs_others(image_bytes: bytes) -> float:
    diff = error_level(load_rgb(image_bytes)[0])
    target = region_mean(diff, BAND)
    others = [region_mean(diff, (0, i * ROW_H, 320, (i + 1) * ROW_H)) for i in range(8) if i != 4]
    return target / (sum(others) / len(others))


def test_edited_region_stands_out_more_than_in_unedited_copy():
    unedited, edited = received_and_edited()
    assert edited_vs_others(edited) > 1.5 * edited_vs_others(unedited)


def test_outputs_have_the_input_size_and_numbers_are_sane():
    result, original, ela_img, heat = analyse(jpeg_bytes(chat_rows(TEXTS)))
    assert original.size == ela_img.size == heat.size == (320, 320)
    assert result.input_format == "JPEG"
    assert 0 <= result.mean_error <= result.p99_error <= result.max_error <= 255
    assert len(result.brightest_blocks) == 5


def test_png_input_gets_lossless_note():
    result, *_ = analyse(png_bytes(chat_rows(TEXTS)))
    assert result.input_format == "PNG"
    assert "not JPEG" in result.note


def test_panel_png_is_three_images_wide():
    png = analyse_to_png(jpeg_bytes(chat_rows(TEXTS)))
    with Image.open(io.BytesIO(png)) as panel:
        assert panel.format == "PNG" and panel.width == 3 * 320


def test_bad_input_and_quality():
    with pytest.raises(ValueError):
        analyse(b"not an image")
    with pytest.raises(ValueError):
        analyse(jpeg_bytes(chat_rows(TEXTS)), quality=30)


# ---- API (mounted on a test app, so this test does not depend on app/main.py) ----
api = FastAPI()
api.include_router(forensics_router, prefix="/api")
client = TestClient(api)
SAMPLE = jpeg_bytes(chat_rows(TEXTS))


def test_api_ela_json():
    resp = client.post("/api/forensics/ela", data={"consent": "true"},
                       files={"file": ("chat.jpg", SAMPLE, "image/jpeg")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["input_format"] == "JPEG" and len(body["sha256"]) == 64
    assert body["quality"] == 90 and len(body["brightest_blocks"]) == 5


def test_api_ela_image_returns_png():
    resp = client.post("/api/forensics/ela/image?quality=95", data={"consent": "true"},
                       files={"file": ("chat.jpg", SAMPLE, "image/jpeg")})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_api_ela_requires_consent_and_image():
    assert client.post("/api/forensics/ela", data={"consent": "false"},
                       files={"file": ("chat.jpg", SAMPLE, "image/jpeg")}).status_code == 400
    assert client.post("/api/forensics/ela", data={"consent": "true"},
                       files={"file": ("notes.txt", b"hello", "text/plain")}).status_code == 415
