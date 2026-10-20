
"""OCR test uses a generated sample image, so it needs a working Tesseract install."""

import io

import pytest
from PIL import Image, ImageDraw

from app.services.ocr import extract_text_from_image_bytes


def test_ocr_extracts_text_from_sample_screenshot():
    # Use a plain white image; Tesseract's exact spacing may vary.
    image = Image.new("RGB", (900, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.text((25, 70), "FardNama evidence test 12345", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    try:
        result = extract_text_from_image_bytes(buffer.getvalue())
    except RuntimeError as exc:
        pytest.skip(str(exc))

    assert "FardNama" in result or "evidence" in result or "12345" in result


def test_ocr_invalid_bytes_raise_value_error():
    with pytest.raises(ValueError):
        extract_text_from_image_bytes(b"not an image")


def test_ocr_missing_tesseract_raises_runtime_error_not_value_error(monkeypatch):
    """TesseractNotFoundError is an OSError; it must surface as RuntimeError, never ValueError."""
    monkeypatch.setenv("TESSERACT_CMD", "/definitely/not/here/tesseract")
    buffer = io.BytesIO()
    Image.new("RGB", (50, 20), "white").save(buffer, format="PNG")

    with pytest.raises(RuntimeError):
        extract_text_from_image_bytes(buffer.getvalue())
