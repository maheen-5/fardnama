
"""Mid-1 live demo: upload -> SHA-256 -> OCR, validation checks, and the Merkle prototype.

Run the server first (from the backend folder):   uvicorn app.main:app --reload
Then, in a second terminal (from the backend folder):

    python demo/demo_core_module.py

Everything printed is also saved to demo/demo_output.txt so it can be attached to the report as
evidence. Only SYNTHETIC sample data is used (never real victim evidence). ASCII-only output so it
works in Windows PowerShell.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import pathlib
import sys
from datetime import datetime

import httpx
from PIL import Image, ImageDraw, ImageFont

# Allow "from app...." when run as `python demo/demo_core_module.py` from the backend folder.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.services.merkle import merkle_root  # noqa: E402

LINES: list[str] = []


def say(text: str = "") -> None:
    print(text)
    LINES.append(text)


def check(label: str, condition: bool) -> bool:
    say(f"  [{'PASS' if condition else 'FAIL'}] {label}")
    return condition


def make_sample_png(text_lines: list[str]) -> bytes:
    """Create a synthetic 'chat screenshot' containing the given lines of text."""
    try:
        font = ImageFont.load_default(size=28)
    except TypeError:  # very old Pillow
        font = ImageFont.load_default()
    image = Image.new("RGB", (1000, 120 + 60 * len(text_lines)), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (30, 30),
        "SYNTHETIC SAMPLE - NOT REAL EVIDENCE",
        fill="gray",
        font=font,
    )
    for i, line in enumerate(text_lines):
        draw.text((30, 100 + 60 * i), line, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def upload(
    client: httpx.Client,
    base: str,
    name: str,
    data: bytes,
    mime: str,
    consent: str = "true",
):
    return client.post(
        f"{base}/api/evidence/upload",
        data={"consent": consent},
        files={"file": (name, data, mime)},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--upload-dir",
        default="data/evidence",
        help="server's evidence folder (to verify stored bytes)",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    failures = 0

    say("=" * 70)
    say(
        "FARDNAMA MID-1 CORE MODULE DEMO   "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    say("=" * 70)

    with httpx.Client(timeout=60) as client:
        # --- 0. health ---------------------------------------------------------------
        say("\n[0] Server health")
        try:
            health = client.get(f"{base}/health").json()
        except httpx.HTTPError as exc:
            say(f"  Cannot reach the server at {base}: {exc}")
            say("  Start it first:  uvicorn app.main:app --reload")
            return 2

        say(f"  /health -> {health}")
        if not check("server is up", health.get("status") == "ok"):
            failures += 1

        ocr = health.get("ocr", {})
        if not check(
            "Tesseract OCR is usable by the SERVER process",
            ocr.get("available") is True,
        ):
            failures += 1
            say(f"      detail: {ocr.get('detail')}")
            say(
                "      Fix: install Tesseract, then restart the terminal running "
                "the server (or set TESSERACT_CMD)."
            )

        # --- 1. main flow: upload -> hash -> OCR ------------------------------------------
        say("\n[1] Upload -> SHA-256 -> OCR (synthetic screenshot)")
        png = make_sample_png(
            ["FardNama evidence test 12345", "You will regret this tomorrow"]
        )
        local_hash = hashlib.sha256(png).hexdigest()
        say(f"  local SHA-256 of the file before upload : {local_hash}")

        response = upload(client, base, "sample_chat.png", png, "image/png")
        say(f"  HTTP status                             : {response.status_code}")
        if not check("upload accepted (201)", response.status_code == 201):
            failures += 1
            say(f"      response: {response.text}")
            return 1

        body = response.json()
        say(f"  evidence_id                             : {body['evidence_id']}")
        say(f"  size_bytes                              : {body['size_bytes']}")
        say(f"  server SHA-256                          : {body['sha256']}")
        say(f"  ocr_status                              : {body['ocr_status']}")
        say(f"  extracted_text                          : {body['extracted_text']!r}")

        failures += not check(
            "server hash equals independently computed hash",
            body["sha256"] == local_hash,
        )
        failures += not check("OCR completed", body["ocr_status"] == "completed")
        text = body["extracted_text"] or ""
        failures += not check(
            "OCR text contains expected words",
            "FardNama" in text or "12345" in text,
        )

        # --- 2. original stored unchanged + tamper detection -------------------------------------
        say("\n[2] Original stored unchanged; tamper detection")
        stored = pathlib.Path(args.upload_dir) / f"{body['evidence_id']}.png"

        if stored.exists():
            stored_bytes = stored.read_bytes()
            failures += not check(
                "stored file is byte-for-byte identical to the upload",
                stored_bytes == png,
            )
            failures += not check(
                "re-hashing the stored file matches the recorded SHA-256",
                hashlib.sha256(stored_bytes).hexdigest() == body["sha256"],
            )

            flipped = bytearray(stored_bytes)
            # Flip a single bit in a COPY; the stored file is not touched.
            flipped[len(flipped) // 2] ^= 0x01
            tampered_hash = hashlib.sha256(bytes(flipped)).hexdigest()
            say(f"  hash after flipping ONE bit in a copy   : {tampered_hash}")
            failures += not check(
                "single-bit change produces a different hash (tamper detected)",
                tampered_hash != body["sha256"],
            )
        else:
            say(
                f"  (stored file not found at {stored}; run from the backend "
                "folder or pass --upload-dir)"
            )

        # --- 3. validation rules ----------------------------------------------------------
        say("\n[3] Validation rules")

        r = upload(
            client,
            base,
            "payload.exe",
            b"not allowed",
            "application/octet-stream",
        )
        failures += not check(
            f"unsupported file type rejected (415) -> got {r.status_code}",
            r.status_code == 415,
        )

        r = upload(
            client,
            base,
            "sample_chat.png",
            png,
            "image/png",
            consent="false",
        )
        failures += not check(
            f"missing consent rejected (400) -> got {r.status_code}",
            r.status_code == 400,
        )

        r = upload(
            client,
            base,
            "broken.png",
            b"this is not a real png",
            "image/png",
        )
        failures += not check(
            f"corrupt image rejected (400) -> got {r.status_code}",
            r.status_code == 400,
        )

        r = upload(client, base, "empty.txt", b"", "text/plain")
        failures += not check(
            f"empty file rejected (400) -> got {r.status_code}",
            r.status_code == 400,
        )

        r = upload(
            client,
            base,
            "note.txt",
            b"plain text evidence",
            "text/plain",
        )
        failures += not check(
            f"plain text accepted, hashed, no OCR (201) -> got {r.status_code}",
            r.status_code == 201
            and r.json()["ocr_status"] == "not_applicable",
        )

        # --- 4. Merkle prototype -----------------------------------------------------------
        say(
            "\n[4] Merkle-root prototype over uploaded evidence hashes "
            "(NOT a custody ledger)"
        )
        hashes = [body["sha256"]]

        for n in (2, 3):
            extra = make_sample_png([f"Synthetic message number {n}"])
            rr = upload(client, base, f"sample_{n}.png", extra, "image/png")
            hashes.append(rr.json()["sha256"])

        root = merkle_root(hashes)
        say(f"  leaves (evidence SHA-256 values): {len(hashes)}")

        for i, h in enumerate(hashes, 1):
            say(f"    leaf {i}: {h}")

        say(f"  Merkle root                     : {root}")
        failures += not check(
            "same leaves give the same root (deterministic)",
            merkle_root(hashes) == root,
        )

        altered = list(hashes)
        altered[1] = hashlib.sha256(b"tampered evidence").hexdigest()
        say(f"  Merkle root after altering leaf 2 : {merkle_root(altered)}")
        failures += not check(
            "altering one leaf changes the root (tamper-evident)",
            merkle_root(altered) != root,
        )
        failures += not check(
            "different evidence sets cannot share a root "
            "(no duplicate-leaf ambiguity)",
            merkle_root(["a", "b", "c"])
            != merkle_root(["a", "b", "c", "c"]),
        )

    say("\n" + "=" * 70)
    say(
        "RESULT: ALL CHECKS PASSED"
        if failures == 0
        else f"RESULT: {failures} CHECK(S) FAILED"
    )
    say("=" * 70)

    out = pathlib.Path(__file__).with_name("demo_output.txt")
    out.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    print(f"\nSaved transcript to {out}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
