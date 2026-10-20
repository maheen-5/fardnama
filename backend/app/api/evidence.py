"""Evidence upload endpoint for the FardNama core pipeline."""
from __future__ import annotations

import io
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.services.hashing import sha256_bytes
from app.services.ocr import extract_text_from_image_bytes

router = APIRouter(tags=["evidence"])

# Local development storage. Set FARDNAMA_UPLOAD_DIR to a protected location in deployment.
UPLOAD_DIR = Path(os.getenv("FARDNAMA_UPLOAD_DIR", "data/evidence"))
MAX_UPLOAD_BYTES = int(os.getenv("FARDNAMA_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

# These are the file types in the current core scope. OCR is performed on supported images.
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".pdf", ".txt", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


@router.post("/evidence/upload", status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    consent: bool = Form(..., description="Explicit per-upload consent to process this evidence."),
):
    """Store original bytes unchanged, hash them, and OCR image evidence."""
    if consent is not True:
        raise HTTPException(status_code=400, detail="Explicit consent is required before processing.")

    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_BYTES}-byte upload limit.")

    # Hash the exact uploaded bytes before OCR or any other processing.
    original_sha256 = sha256_bytes(content)

    # Verify image bytes actually represent an image (don't trust the extension alone).
    extracted_text = None
    ocr_status = "not_applicable"
    if extension in IMAGE_EXTENSIONS:
        # Step 1: is it a decodable image? Only a failure here is a "bad image" (HTTP 400).
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise HTTPException(status_code=400, detail="The uploaded image could not be decoded.") from exc

        # Step 2: OCR. Kept separate so an OCR/Tesseract problem is never reported as a bad image.
        try:
            extracted_text = extract_text_from_image_bytes(content)
            ocr_status = "completed"
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="The uploaded image could not be decoded.") from exc
        except RuntimeError as exc:
            # OCR dependency/configuration problems are server-side: report them clearly.
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Preserve the original upload byte-for-byte. A generated ID avoids using user filenames as paths.
    evidence_id = str(uuid.uuid4())
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / f"{evidence_id}{extension}"
    stored_path.write_bytes(content)

    return {
        "evidence_id": evidence_id,
        "filename": original_name,
        "size_bytes": len(content),
        "sha256": original_sha256,
        "ocr_status": ocr_status,
        "extracted_text": extracted_text,
        "message": "Evidence uploaded; original bytes stored unchanged.",
    }
