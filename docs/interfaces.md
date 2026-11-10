# FardNama: Interfaces Provided by Sections 5, 6/7 and 15

| | |
|---|---|
| **Status** | Draft v0.1, for agreement |
| **Owner** | Muhammad Noor Ul Azeem (Sections 5, 6, 7, 15) |
| **Reviewers** | Zainab Waqas, Maheen Ahmad |
| **Used by** | Section 1 (pipeline), 8 (severity), 9 (report), 11 (Flutter), 15 (SLM) |

This file fixes the shape of three outputs so that each section can be built in parallel. Until the real code is ready, other sections can work against the mock examples given below.

---

## 0. Rules for all three interfaces

1. **Format.** JSON, `snake_case` field names, UTF-8. Timestamps are ISO 8601 in UTC (for example `2026-11-09T11:00:00Z`).
2. **Versioning.** Every response carries `schema_version`. A field may be added without breaking anyone; renaming or removing a field needs a new version and approval from both reviewers.
3. **Missing values.** A value that does not apply is sent as `null`. The field is never left out, so readers do not need to check whether a key exists.
4. **Custody hash.** When a result is written to the custody log, `output_hash` is the SHA-256 of the result's canonical JSON: keys sorted, separators `(",", ":")`, UTF-8, no extra whitespace. This produces the 32-byte value that `compute_entry_hash()` in `app/models/ledger.py` expects.
   ```python
   json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
   ```
5. **Errors.** Errors use the same codes as the existing forensics API, with FastAPI's `{"detail": "..."}` body:
   - `400`: missing consent, or input that cannot be read
   - `413`: input too large
   - `415`: wrong file type
   - `422`: request validation error
6. **Consent.** Public endpoints require `consent=true`, as the forensics endpoints already do. The internal Python functions called by the upload pipeline do not ask again, because consent was recorded at upload.
7. **Wording.** Forensics and classification results are **indicators for a human reviewer**, not proof. Screens and reports must keep the `disclaimer` text.

---

## 1. Classification result (Sections 6 and 7)

### How it is called

| Caller | Call |
|---|---|
| Pipeline (Section 1) | `classify_text(text: str) -> dict` (internal Python function) |
| Direct / testing | `POST /api/classify`, JSON body `{"text": "...", "consent": true}` |

The input is the OCR text of one evidence item. In FYP-1 the whole extracted text is classified as one unit; splitting a screenshot into separate messages is not in FYP-1 scope.

### Response

```json
{
  "schema_version": "1.0",
  "status": "ok",
  "label": "Harassment",
  "confidence": 0.82,
  "scores": {
    "Threat": 0.03,
    "Hate_speech": 0.10,
    "Harassment": 0.82,
    "Neutral": 0.05
  },
  "low_confidence": false,
  "doxxing": {
    "detected": false,
    "match_types": []
  },
  "language": "roman_urdu",
  "input_sha256": "9f2c…e41a",
  "model": {
    "name": "svm-tfidf",
    "version": "v1",
    "dataset_version": "v1",
    "taxonomy_version": 1
  },
  "created_at": "2026-11-09T11:00:00Z",
  "disclaimer": "Automated indicator for a human reviewer; not a finding."
}
```

### Fields

| Field | Type | Meaning |
|---|---|---|
| `status` | `"ok"` or `"skipped_empty_text"` | `skipped_empty_text` when OCR produced no usable text. In that case `label`, `confidence` and `scores` are `null`. |
| `label` | string or null | One of `Threat`, `Hate_speech`, `Harassment`, `Neutral`, as defined in `fardnama-data/config/taxonomy.yaml`. |
| `confidence` | number 0–1 or null | Calibrated probability of `label`. The SVM is wrapped with `CalibratedClassifierCV`, because LinearSVC alone gives scores, not probabilities. |
| `scores` | object or null | Calibrated probability for every label the model knows. Values add up to 1. |
| `low_confidence` | boolean | `true` when `confidence` is below the threshold in config (default 0.5, to be agreed). The UI should ask for human review. |
| `doxxing` | object | Result of the pattern-based Doxxing detector (Section 6), kept separate from the model's label. `match_types` lists only the kinds of identifier found (`phone_number`, `cnic`, `email`, `address`), **never the values themselves**, so no personal data is copied into results or logs. |
| `language` | string or null | Best-effort guess: `english`, `roman_urdu`, `urdu_script`, or `null` if unsure. |
| `input_sha256` | string | SHA-256 of the exact text that was classified, linking the result to the OCR output. |
| `model` | object | Which model produced the result. Needed to trace evidence, and to compare SVM and DistilBERT/XLM-R later. |

Doxxing is not a model label in FYP-1, because there is no labelled training data for it. It is reported only through `doxxing`.

### Who uses it

| Section | Uses |
|---|---|
| 1 Pipeline (Zainab) | Stores the whole object with the evidence item, and writes a custody event with stage `CLASSIFY` |
| 8 Severity (Zainab) | `label`, `confidence`, `doxxing.detected` |
| 9 Report (Zainab) | `label`, `confidence`, `doxxing.match_types`, `model.name`, `disclaimer` |
| 11 Flutter (Maheen) | `label`, `confidence`, `low_confidence`, `disclaimer` |
| 15 SLM (Noor) | `label`, `doxxing.match_types` as part of the summary input |

When the language-model classifier (Section 7) replaces the SVM, only `model` changes. Every other field keeps the same meaning.

---

## 2. Forensics result (Section 5)

### How it is called

| Caller | Call |
|---|---|
| Pipeline (Section 1) | `analyse_image(image_bytes: bytes, case_phashes: list[dict]) -> dict` |

`case_phashes` holds the existing evidence in the same case, as `[{"evidence_id": "...", "phash": "..."}]`, so that near-duplicates can be found. It is supplied by the pipeline from stored results.

The existing endpoints (`/api/forensics/phash`, `/phash/compare`, `/ela`, `/ela/image`) stay as they are.

### Response

```json
{
  "schema_version": "1.0",
  "image_sha256": "3b7d…90cc",
  "input_format": "JPEG",
  "phash": {
    "value": "c3a1…7f",
    "hash_bits": 256
  },
  "similar_evidence": [
    {
      "evidence_id": "ev_0007",
      "distance": 2,
      "distance_fraction": 0.0078,
      "verdict": "near_duplicate"
    }
  ],
  "ela": {
    "quality": 90,
    "mean_error": 1.84,
    "p99_error": 14.0,
    "max_error": 61,
    "block_size": 16,
    "brightest_blocks": [{"x": 128, "y": 640, "w": 16, "h": 16, "mean_error": 22.5}],
    "note": ""
  },
  "ela_panel_ref": null,
  "notes": [],
  "created_at": "2026-11-09T11:00:00Z",
  "disclaimer": "Forensic indicators for a human reviewer; they do not prove or rule out manipulation."
}
```

### Fields

| Field | Type | Meaning |
|---|---|---|
| `image_sha256` | string | SHA-256 of the working copy that was analysed. |
| `phash.value` | string | 256-bit perceptual hash as hex. |
| `similar_evidence` | list | Evidence in the same case with verdict `near_duplicate` (≤10% bits differ) or `possibly_related` (≤25%). Items judged `different` are left out. An empty list means there is no match. |
| `ela` | object or null | Values from `ELAResult` in `app/services/ela.py`. `null` for non-JPEG input, because ELA needs compression history. |
| `ela_panel_ref` | string or null | Storage reference of the 3-panel PNG (original, ELA, heatmap). The forensics function returns the PNG bytes separately, and the pipeline stores them through the storage service (Section 4) and fills this field. |
| `notes` | list of strings | Warnings for the reviewer, for example `"PNG is lossless; ELA is not applicable and would show edges only."` |

### Who uses it

| Section | Uses |
|---|---|
| 1 Pipeline (Zainab) | Stores the object, stores the ELA panel, and writes a custody event with stage `FORENSICS` |
| 9 Report (Zainab) | `similar_evidence`, the ELA panel, `notes`, `disclaimer` |
| 11 Flutter (Maheen) | Same as the report, plus the heatmap image on the evidence detail screen |
| 15 SLM (Noor) | `similar_evidence` verdicts and `notes` as part of the summary input |

---

## 3. SLM case summary (Section 15)

Generating a summary may take seconds or longer on our hardware, so the endpoint works asynchronously.

### Endpoints

| Call | Purpose |
|---|---|
| `POST /api/cases/{case_id}/summary` | Starts generation. Returns `202` with `status: "pending"`. |
| `GET /api/cases/{case_id}/summary` | Returns the latest summary and its status. The client polls until `status` is `ready` or `failed`. |

The SLM service builds its own input from data already stored for the case: OCR text, classification results and forensics results. Callers send nothing except `case_id`.

### Response

```json
{
  "schema_version": "1.0",
  "case_id": "case_0012",
  "status": "ready",
  "summary": "The case contains three screenshots from one sender sent between 2 and 5 November. Two messages were classified as harassment. One screenshot is a near-duplicate of another. No threat or personal identifiers were detected.",
  "evidence_used": ["ev_0005", "ev_0006", "ev_0007"],
  "missing_info": ["Sender identity is not visible in the screenshots."],
  "language": "en",
  "model": {
    "name": "phi-4-mini",
    "quantisation": "q4",
    "prompt_version": "summarizer-v1"
  },
  "generated_at": "2026-11-09T11:02:10Z",
  "error": null,
  "disclaimer": "Automatically generated summary; check it against the evidence before use."
}
```

### Fields

| Field | Type | Meaning |
|---|---|---|
| `status` | `pending`, `ready` or `failed` | `summary` is `null` unless `status` is `ready`. |
| `summary` | string or null | Short factual summary, at most about 150 words, in English for FYP-1. It states only facts present in the stored evidence and results. |
| `evidence_used` | list | IDs of the evidence items given to the model. |
| `missing_info` | list of strings | Information the model was told to look for but could not find (guardrail). |
| `model` | object | Model, quantisation and prompt version used, so a summary can be reproduced. |
| `error` | string or null | Short reason when `status` is `failed`. |

### Who uses it

| Section | Uses |
|---|---|
| 9 Report (Zainab) | `summary`, `missing_info`, `disclaimer` in the report's summary slot |
| 11 Flutter (Maheen) | Starts generation, polls `GET`, shows `summary` and `disclaimer` in the case view |

---

## 4. Open questions to agree before coding

| # | Question | Proposal | Decided by |
|---|---|---|---|
| 1 | `low_confidence` threshold | 0.5, revisited after calibration results | Noor and Zainab (severity) |
| 2 | Should the SLM summary be a custody event? | Yes. Add stage `SUMMARY` to `_ALLOWED_STAGES` in `ledger.py` | Zainab (ledger owner) |
| 3 | Where is the ELA panel stored? | Through the storage service, encrypted like other derived files | Zainab (storage owner) |
| 4 | How does Doxxing affect severity? | `doxxing.detected = true` raises severity by one level | Zainab (severity owner) |
| 5 | Polling interval in Flutter for the summary | Every 3 seconds, stop after 2 minutes | Maheen |
| 6 | Language of the summary | English only in FYP-1 | All |

---

## 5. Agreement

| Member | Section(s) | Agreed (date) |
|---|---|---|
| Muhammad Noor Ul Azeem | 5, 6, 7, 15 (provider) | |
| Zainab Waqas | 1, 8, 9 (user) | |
| Maheen Ahmad | 11 (user) | |

Changes after agreement go through a pull request that changes `schema_version` and is reviewed by both reviewers.
