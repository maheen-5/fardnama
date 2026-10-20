
"""OCR helper for image evidence using Tesseract via pytesseract.

Error contract (important for the upload endpoint):
  * ValueError   -> the bytes are not a readable image          (client problem, HTTP 400)
  * RuntimeError -> OCR itself is unavailable or failed         (server problem, HTTP 503)

Note: pytesseract.TesseractNotFoundError is a subclass of OSError. The Tesseract errors
must therefore be caught BEFORE any generic OSError handler, otherwise a missing Tesseract
install is wrongly reported as "invalid image".
"""
from __future__ import annotations

import io
import os
import shutil

from PIL import Image, UnidentifiedImageError

# Default install location of the Windows installer (UB-Mannheim build).
_WINDOWS_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

_MISSING_MESSAGE = (
    "Tesseract OCR was not found by the server process. Install Tesseract and either "
    "add it to PATH (then restart the terminal running the server) or set the "
    "TESSERACT_CMD environment variable to the full path of tesseract.exe."
)


def _configure_tesseract(pytesseract) -> None:
    """Point pytesseract at the executable: TESSERACT_CMD, else PATH, else the Windows default.

    Recomputed on every call so no stale path is left behind between calls.
    """
    explicit = os.getenv("TESSERACT_CMD")
    if explicit:
        command = explicit
    elif shutil.which("tesseract") is None and os.path.exists(_WINDOWS_DEFAULT):
        command = _WINDOWS_DEFAULT
    else:
        command = "tesseract"
    pytesseract.pytesseract.tesseract_cmd = command


def ocr_status() -> dict:
    """Report whether OCR is usable (used by /health and for demo troubleshooting)."""
    try:
        import pytesseract
    except ImportError:
        return {"available": False, "detail": "pytesseract is not installed"}
    _configure_tesseract(pytesseract)
    try:
        return {
            "available": True,
            "tesseract_version": str(pytesseract.get_tesseract_version()),
        }
    except pytesseract.TesseractNotFoundError:
        return {"available": False, "detail": _MISSING_MESSAGE}


def extract_text_from_image_bytes(image_bytes: bytes, language: str = "eng") -> str:
    """Extract text from image bytes. Requires Tesseract installed on the host."""
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependency is missing. Install Python requirements and the Tesseract "
            "OCR system package."
        ) from exc

    _configure_tesseract(pytesseract)

    # Step 1: decode the image. Only failures here mean "bad image".
    try:
        with Image.open(io.BytesIO(image_bytes)) as opened:
            image = opened.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid or unreadable image bytes.") from exc

    # Step 2: run OCR. Tesseract errors are caught first (TesseractNotFoundError is an OSError).
    try:
        return pytesseract.image_to_string(image, lang=language).strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(_MISSING_MESSAGE) from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError(f"Tesseract OCR failed: {exc}") from exc
