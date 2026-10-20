# FardNama - Mid-1 Test Report (core module)

**Scope:** upload -> SHA-256 -> OCR core module, and the Merkle-root prototype.
**Run on:** _<date / machine / Python version / Tesseract version>_
**Command:** `python -m pytest -v` (from `backend/`)

## Result summary

| Suite | Tests run | Passed | Failed | Skipped |
|-------|-----------|--------|--------|---------|
| Backend (`pytest`) | _<n>_ | _<n>_ | _<n>_ | _<n>_ |

Paste the real `pytest -v` output below (or attach a screenshot):

```
<paste pytest -v output here>
```

## Test inventory

| Test | File | Purpose | Requirement |
|------|------|---------|-------------|
| `test_sha256_hash_deterministic` | test_hashing.py | Same bytes give same hash | FR3 |
| `test_sha256_hash_changes_on_single_bit_flip` | test_hashing.py | One-bit change alters hash | FR3 |
| `test_merkle_tree_single_leaf` | test_merkle.py | Single-leaf tree is valid and correct | FR4 (prototype) |
| `test_merkle_tree_odd_number_of_leaves` | test_merkle.py | Odd leaf promoted; expected structure | FR4 (prototype) |
| `test_merkle_root_changes_on_tamper` | test_merkle.py | Altering a leaf changes the root | FR4 (prototype) |
| `test_merkle_tamper_detected_at_every_position` | test_merkle.py | Tamper at each of 7 positions detected | FR4 (prototype) |
| `test_merkle_root_depends_on_order` | test_merkle.py | Leaf order matters | FR4 (prototype) |
| `test_merkle_odd_node_is_not_duplicated` | test_merkle.py | `[a,b,c]` and `[a,b,c,c]` differ (regression) | FR4 (prototype) |
| `test_merkle_empty_tree_is_defined_and_distinct` | test_merkle.py | Empty tree defined | FR4 (prototype) |
| `test_merkle_expected_root_for_two_leaves` | test_merkle.py | Known-answer check | FR4 (prototype) |
| `test_ocr_extracts_text_from_sample_screenshot` | test_ocr.py | OCR reads a generated screenshot | FR2 |
| `test_ocr_invalid_bytes_raise_value_error` | test_ocr.py | Bad bytes -> ValueError | FR2 |
| `test_ocr_missing_tesseract_raises_runtime_error_not_value_error` | test_ocr.py | Missing Tesseract is not a "bad image" | FR2 |
| `test_upload_rejects_unsupported_file_type` | test_upload.py | `.exe` -> 415 | FR1 |
| `test_upload_requires_consent` | test_upload.py | No consent -> 400 | FR13 |
| `test_upload_image_returns_hash_and_ocr_status` | test_upload.py | 201, hash, OCR, stored bytes identical | FR1, FR2, FR3 |
| `test_upload_corrupt_image_returns_400` | test_upload.py | Corrupt image -> 400, nothing stored | FR1 |
| `test_upload_empty_file_returns_400` | test_upload.py | Empty file -> 400 | FR1 |
| `test_upload_oversize_file_returns_413` | test_upload.py | Over size limit -> 413 | FR1 |
| `test_upload_text_file_is_hashed_and_stored_unchanged` | test_upload.py | Non-image path: hash + unchanged storage | FR1, FR3 |
| `test_missing_tesseract_is_503_not_a_decode_error` | test_upload.py | Regression for the 400 bug | FR2 |

## Defects found and fixed during Mid-1

| # | Defect | Cause | Fix | Regression test |
|---|--------|-------|-----|-----------------|
| 1 | Valid PNG uploads returned 400 "could not be decoded" | `TesseractNotFoundError` is an `OSError`; `ocr.py` caught `OSError` first and re-raised it as `ValueError`, which the endpoint reported as a decode error. The server process could not see Tesseract. | Tesseract errors caught first and raised as `RuntimeError` (HTTP 503 with a clear message); decode and OCR steps separated; `TESSERACT_CMD` / default Windows path support; `/health` reports OCR status. | `test_missing_tesseract_is_503_not_a_decode_error`, `test_ocr_missing_tesseract_raises_runtime_error_not_value_error` |
| 2 | Different evidence sets could give the same Merkle root | Odd level duplicated the last node, so `[a,b,c]` and `[a,b,c,c]` collided. | Odd node is promoted unchanged. | `test_merkle_odd_node_is_not_duplicated` |

## Live demo evidence

`python demo\demo_core_module.py` -> transcript saved in `backend/demo/demo_output.txt`.
Screenshots: _<attach>_

## Limitations (honest scope)

- Local file storage is a placeholder; private IPFS storage, encryption and Ethereum anchoring are Final-1.
- Only the original upload is hashed at Mid-1; the separate working-copy hash is Final-1.
- OCR uses the English Tesseract model (`eng`); Roman Urdu text accuracy is not evaluated.
- The Merkle code is a utility prototype, not a custody ledger.
