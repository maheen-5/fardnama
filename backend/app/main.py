"""FastAPI entry point for the FardNama evidence core module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.evidence import router as evidence_router
from app.api.forensics import router as forensics_router
from app.services.ocr import ocr_status

app = FastAPI(
    title="FardNama Evidence Core API",
    version="0.1.0",
    description="Evidence upload, SHA-256 integrity hashing, and OCR extraction.",
)

# Development convenience. Restrict this list to the real frontend origin before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(evidence_router, prefix="/api")
app.include_router(forensics_router, prefix="/api")


@app.get("/health")
def health():
    """Health check; also reports whether OCR (Tesseract) is usable by THIS server process."""
    return {"status": "ok", "ocr": ocr_status()}
