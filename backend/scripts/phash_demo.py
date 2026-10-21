"""pHash prototype demo: compare one reference image against other images.

For every image it prints the SHA-256 result (Zainab's hashing service) next to the pHash
result, which shows the point of having both:
  - SHA-256 changes for ANY re-save / resize / edit  -> proves byte-level integrity
  - pHash stays close for visually identical copies  -> finds the same picture again

"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.hashing import sha256_bytes  # noqa: E402  (Zainab's service, unchanged)
from app.services.phash import (  # noqa: E402
    DEFAULT_HASH_SIZE, NEAR_DUPLICATE_MAX_FRACTION, RELATED_MAX_FRACTION,
    compare_hashes, phash_bytes,
)

SAMPLES = BACKEND / "forensics_samples"
RESULTS = BACKEND / "forensics_results"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def default_inputs() -> list[Path]:
    ref = SAMPLES / "original.png"
    if not ref.exists():
        sys.exit("forensics_samples/original.png not found: "
                 "the sample images must be in backend/forensics_samples/")
    others = sorted(p for p in SAMPLES.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES and p != ref)
    return [ref, *others]


def main() -> None:
    ap = argparse.ArgumentParser(description="pHash prototype demo")
    ap.add_argument(
        "images",
        nargs="*",
        type=Path,
        help="reference image first, then images to compare")
    ap.add_argument(
        "--hash-size",
        type=int,
        default=DEFAULT_HASH_SIZE,
        help="8 = 64-bit, 16 = 256-bit (default)")
    args = ap.parse_args()

    paths = args.images or default_inputs()
    if len(paths) < 2:
        sys.exit("Give a reference image and at least one image to compare.")
    ref, others = paths[0], paths[1:]
    ref_bytes = ref.read_bytes()
    ref_sha = sha256_bytes(ref_bytes)
    ref_hash = phash_bytes(ref_bytes, args.hash_size)

    rows = []
    for path in others:
        data = path.read_bytes()
        result = compare_hashes(ref_hash, phash_bytes(data, args.hash_size))
        rows.append({
            "image": path.name,
            "sha256_same_as_reference": sha256_bytes(data) == ref_sha,
            **result.to_dict(),
        })

    bits = rows[0]["hash_bits"]
    print(f"\nReference: {ref.name}   pHash ({bits}-bit): {ref_hash}")
    print(f"Thresholds: near_duplicate <= {NEAR_DUPLICATE_MAX_FRACTION:.0%}, "
          f"possibly_related <= {RELATED_MAX_FRACTION:.0%} of bits differ\n")
    print(f"{'Image':28s} {'SHA-256 same?':14s} {'Bits differ':>12s} {'Similarity':>11s}  Verdict")
    print("-" * 82)
    for r in rows:
        print(f"{r['image']:28s} {('yes' if r['sha256_same_as_reference'] else 'no'):14s} "
              f"{r['distance']:>5d} ({r['distance_fraction']:>5.1%}) "
              f"{r['similarity']:>10.1%}  {r['verdict']}")

    RESULTS.mkdir(exist_ok=True)
    report = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "reference": ref.name,
        "reference_phash": ref_hash,
        "hash_bits": bits,
        "thresholds": {"near_duplicate_max_fraction": NEAR_DUPLICATE_MAX_FRACTION,
                       "possibly_related_max_fraction": RELATED_MAX_FRACTION},
        "comparisons": rows,
    }
    suffix = "" if args.hash_size == DEFAULT_HASH_SIZE else f"_{bits}bit"
    (RESULTS / f"phash_report{suffix}.json").write_text(json.dumps(report,
                                                                   indent=2), encoding="utf-8")

    md = [
        f"# pHash prototype results ({bits}-bit)",
        "",
        f"Generated {report['generated']}. Reference image: `{ref.name}` (pHash `{ref_hash}`).",
        f"Verdict rule: near_duplicate if ≤ {NEAR_DUPLICATE_MAX_FRACTION:.0%} of bits differ, "
        f"possibly_related if ≤ {RELATED_MAX_FRACTION:.0%}, otherwise different.",
        "",
        "| Image | SHA-256 same? | Bits differ | Similarity | pHash verdict |",
        "|---|---|---|---|---|",
        *[f"| {r['image']} | {'yes' if r['sha256_same_as_reference'] else 'no'} | "
          f"{r['distance']} / {r['hash_bits']} ({r['distance_fraction']:.1%}) | "
          f"{r['similarity']:.1%} | {r['verdict']} |"
          for r in rows],
        "",
        "## How to read this",
        "",
        "- SHA-256 differs for every variant: any re-save or edit changes the bytes. "
        "That is the integrity check.",
        "- pHash stays close for copies that look the same (resized, recompressed). "
        "That is how the system can",
        "  recognise the same screenshot uploaded twice or forwarded through another app.",
        "- pHash is a similarity measure, not proof of manipulation. "
        "A small local edit (one changed message) can",
        "  stay close to the original; different chats in the same app can look partly similar "
        "because of the layout.",
        "",
    ]
    (RESULTS / f"phash_report{suffix}.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved forensics_results/phash_report{suffix}.md and .json")


if __name__ == "__main__":
    main()
