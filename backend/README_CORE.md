# FardNama core evidence module (starter implementation)

This module implements the assigned core pipeline: evidence upload, SHA-256 hashing of the
original bytes before processing, and OCR for image evidence. It also includes a small Merkle
root helper and tests for the report's core edge cases.

## Important scope notes

- Local file storage is used as a development placeholder; this is not the report's planned private IPFS storage.
- Merkle code is a local prototype helper, not blockchain anchoring.
- OCR supports images only in this core implementation. Other accepted file types are preserved and hashed, but are not OCR-processed.
- Tesseract must be installed separately on the computer running the backend.
- Before deployment, restrict CORS, add authentication/authorization and case-level access controls, configure protected storage, and review privacy/security requirements.
- Do not test with real victims' sensitive evidence; use synthetic/sample files.

## Run locally (from the repository root)

1. Create and activate a Python virtual environment.
2. Install `backend/requirements.txt`.
3. Install the Tesseract OCR system executable for your OS.
4. From the `backend` directory, run `uvicorn app.main:app --reload`.
5. Open `http://127.0.0.1:8000/docs` to view the API.
6. Run tests from `backend`: `python -m pytest -q`.

The upload endpoint is `POST /api/evidence/upload` and accepts multipart fields:
- `file`: evidence file
- `consent`: `true` (explicit consent is required)

Allowed extensions are configured in `app/api/evidence.py`. Change them only if the SRS/team decision supports it.


## Windows quick start (PowerShell, from the `backend` folder)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Install Tesseract (UB-Mannheim Windows build), then CLOSE AND REOPEN PowerShell so PATH refreshes.
uvicorn app.main:app --reload          # terminal 1: the server
python -m pytest -v                    # terminal 2: tests
python demo\demo_core_module.py        # terminal 2: live demo, saves demo\demo_output.txt
```

## Troubleshooting

**Upload returns an error about Tesseract / OCR (HTTP 503).** The *server* process cannot find Tesseract.
Open `http://127.0.0.1:8000/health` - the `ocr.available` field tells you what the server sees.
A terminal opened before Tesseract was installed keeps the old PATH, so restart the terminal that runs
`uvicorn`. Alternatively set the path explicitly before starting the server:

```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
uvicorn app.main:app --reload
```

(On Windows the default install location is tried automatically.)

**Upload returns 400 "could not be decoded".** The file really is not a valid image (corrupt or wrong
extension). A missing Tesseract is no longer reported this way.

## Status codes of `POST /api/evidence/upload`

| Code | Meaning |
|------|---------|
| 201 | Stored unchanged, SHA-256 returned, OCR done (images) |
| 400 | Consent not given, empty file, or image cannot be decoded |
| 413 | File larger than 10 MB |
| 415 | File extension not allowed |
| 422 | Missing form field (`file` or `consent`) |
| 503 | OCR unavailable on the server (Tesseract missing/misconfigured) |

## Merkle prototype note

`app/services/merkle.py` is a Mid-1 prototype of the integrity primitive. Odd nodes are promoted, not
duplicated, so `[a, b, c]` and `[a, b, c, c]` have different roots. It is not a custody ledger and nothing is
anchored on a blockchain; custody-chain integration and Ethereum anchoring are Final-1 work.
