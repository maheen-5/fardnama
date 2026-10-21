"""Image-forensics prototype endpoints (FYP-1 Mid).

Perceptual hashing (pHash) and error level analysis (ELA).

These endpoints only analyse the uploaded images and return results; they do not store
anything. Upload limits and accepted image types are reused from the evidence endpoint
(app/api/evidence.py) so both parts of the API follow the same rules.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile

from app.api.evidence import IMAGE_EXTENSIONS, MAX_UPLOAD_BYTES, enforce_pixel_limit
from app.services.ela import DEFAULT_QUALITY, analyse, analyse_to_png
from app.services.hashing import sha256_bytes
from app.services.phash import DEFAULT_HASH_SIZE, compare_images, phash_bytes

router = APIRouter(prefix="/forensics", tags=["forensics (prototype)"])

HASH_SIZE_QUERY = Query(
    DEFAULT_HASH_SIZE,
    ge=4,
    le=32,
    description="8 = 64-bit pHash, 16 = 256-bit (default)")
QUALITY_QUERY = Query(
    DEFAULT_QUALITY,
    ge=50,
    le=99,
    description="JPEG quality used for the ELA re-save")


async def _read_image(upload: UploadFile) -> bytes:
    name = Path(upload.filename or "").name
    if not name or Path(name).suffix.lower() not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=415, detail=f"'{
                name or 'file'}' is not a supported image. Allowed: {
                ', '.join(
                    sorted(IMAGE_EXTENSIONS))}", )
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail=f"'{name}' is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"'{name}' exceeds the {MAX_UPLOAD_BYTES}-byte upload limit.")
    enforce_pixel_limit(content)
    return content


def _require_consent(consent: bool) -> None:
    if consent is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent is required before processing.")


@router.post("/phash")
async def phash_single(
    file: UploadFile = File(...),
    consent: bool = Form(..., description="Explicit consent to process this image."),
    hash_size: int = HASH_SIZE_QUERY,
):
    """Return the perceptual hash (and SHA-256) of one image."""
    _require_consent(consent)
    data = await _read_image(file)
    try:
        value = phash_bytes(data, hash_size)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image could not be decoded.") from exc
    return {"filename": Path(file.filename).name, "sha256": sha256_bytes(data),
            "phash": value, "hash_bits": hash_size * hash_size}


@router.post("/phash/compare")
async def phash_compare(
    file_a: UploadFile = File(..., description="First image (e.g. the original screenshot)"),
    file_b: UploadFile = File(..., description="Second image to compare against the first"),
    consent: bool = Form(..., description="Explicit consent to process both images."),
    hash_size: int = HASH_SIZE_QUERY,
):
    """Compare two images: SHA-256 equality (exact bytes) and pHash similarity (visual)."""
    _require_consent(consent)
    a, b = await _read_image(file_a), await _read_image(file_b)
    try:
        result = compare_images(a, b, hash_size)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="One of the uploaded images could not be decoded.") from exc
    return {
        "file_a": Path(file_a.filename).name,
        "file_b": Path(file_b.filename).name,
        "sha256_identical": sha256_bytes(a) == sha256_bytes(b),
        **result.to_dict(),
        "note": ("pHash measures visual similarity only; "
                 "it does not prove or rule out manipulation."),
    }


@router.post("/ela")
async def ela_numbers(
    file: UploadFile = File(...),
    consent: bool = Form(..., description="Explicit consent to process this image."),
    quality: int = QUALITY_QUERY,
):
    """Error level analysis: summary numbers and the brightest blocks to review (JSON)."""
    _require_consent(consent)
    data = await _read_image(file)
    try:
        result, *_ = analyse(data, quality=quality)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image could not be decoded.") from exc
    return {"filename": Path(file.filename).name, "sha256": sha256_bytes(data), **result.to_dict()}


@router.post(
    "/ela/image",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}, "description": "Original | ELA | heatmap"}},
)
async def ela_image(
    file: UploadFile = File(...),
    consent: bool = Form(..., description="Explicit consent to process this image."),
    quality: int = QUALITY_QUERY,
):
    """Error level analysis as a picture: original, ELA and heatmap side by side (PNG)."""
    _require_consent(consent)
    data = await _read_image(file)
    try:
        png = analyse_to_png(data, quality=quality)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image could not be decoded.") from exc
    return Response(content=png, media_type="image/png")
