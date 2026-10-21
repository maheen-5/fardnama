"""ELA prototype demo.

For each image it saves a 3-panel picture (original | ELA | heatmap) and records the numbers.
On the synthetic samples it also checks the prototype against the known edit: how much brighter
the edited chat message is than the other messages, in the edited JPEG versus the unedited one.

Writes forensics_results/ela/<image>_ela_panel.png, forensics_results/ela_report.md and .json.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.ela import (  # noqa: E402
    DEFAULT_QUALITY, analyse, error_level, load_rgb, panel, region_mean,
)

SAMPLES = BACKEND / "forensics_samples"
ELA_SAMPLES = SAMPLES / "ela"
RESULTS = BACKEND / "forensics_results"


def default_inputs() -> list[Path]:
    wanted = [ELA_SAMPLES / n for n in ("jpeg_original.jpg", "jpeg_resaved.jpg", "jpeg_edited.jpg")]
    wanted.append(SAMPLES / "original.png")      # PNG: shows the lossless-input limitation
    missing = [p for p in wanted if not p.exists()]
    if missing:
        sys.exit("Samples not found: expected the JPEG samples in backend/forensics_samples/ela/")
    return wanted


def edit_check(quality: int) -> list[dict]:
    """Edited message vs other messages, in the unedited and the edited JPEG."""
    regions_file = ELA_SAMPLES / "edit_regions.json"
    if not regions_file.exists():
        return []
    regions = json.loads(regions_file.read_text(encoding="utf-8"))
    rows = []
    for name in ("jpeg_resaved.jpg", "jpeg_edited.jpg"):
        image, _ = load_rgb((ELA_SAMPLES / name).read_bytes())
        diff = error_level(image, quality)
        target = region_mean(diff, tuple(regions["edited_message"]))
        others = [region_mean(diff, tuple(b)) for b in regions["other_messages"]]
        avg = sum(others) / len(others)
        rows.append({
            "image": name,
            "edited_message_error": round(target, 3),
            "other_messages_avg_error": round(avg, 3),
            "other_messages_max_error": round(max(others), 3),
            "ratio": round(target / avg, 2) if avg else None,
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="ELA prototype demo")
    ap.add_argument("images", nargs="*", type=Path)
    ap.add_argument("--quality", type=int, default=DEFAULT_QUALITY,
                    help="JPEG re-save quality (default 90)")
    args = ap.parse_args()

    out_dir = RESULTS / "ela"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in args.images or default_inputs():
        result, original, ela_img, heat = analyse(path.read_bytes(), quality=args.quality)
        panel_path = out_dir / f"{path.stem}_ela_panel.png"
        panel(original, ela_img, heat).save(panel_path)
        rows.append({"image": path.name, "panel": f"ela/{panel_path.name}", **result.to_dict()})

    print(f"\nELA at JPEG quality {args.quality}\n")
    print(f"{'Image':22s} {'Format':7s} {'Mean err':>9s} {'P99 err':>8s} {'Max err':>8s}  Panel")
    print("-" * 80)
    for r in rows:
        print(f"{r['image']:22s} {r['input_format']:7s} {r['mean_error']:>9.3f} "
              f"{r['p99_error']:>8.0f} {r['max_error']:>8d}  forensics_results/{r['panel']}")

    check = [] if args.images else edit_check(args.quality)
    if check:
        print("\nCheck against the known edit (average error, 0-255 scale):")
        print(
            f"{
                'Image':20s} {
                'Edited message':>15s} {
                'Other msgs avg':>15s} {
                    'Other msgs max':>15s} {
                        'Ratio':>7s}")
        for c in check:
            print(
                f"{
                    c['image']:20s} {
                    c['edited_message_error']:>15.3f} {
                    c['other_messages_avg_error']:>15.3f} " f"{
                    c['other_messages_max_error']:>15.3f} {
                        c['ratio']:>6.2f}x")

    report = {"generated": datetime.now().isoformat(timespec="seconds"), "quality": args.quality,
              "images": rows, "edit_check": check}
    (RESULTS / "ela_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# ELA prototype results",
        "",
        f"Generated {report['generated']}. "
        f"Each image is re-saved as JPEG at quality {args.quality}; "
        "the error level is how much each pixel changed (0-255).",
        "",
        "| Image | Format | Mean error | 99th pct | Max | Panel |",
        "|---|---|---|---|---|---|",
        *[f"| {r['image']} | {r['input_format']} | {r['mean_error']:.3f} | "
          f"{r['p99_error']:.0f} | {r['max_error']} | ![{r['image']}]({r['panel']}) |"
          for r in rows],
        "",
    ]
    if check:
        md += [
            "## Check against the known edit",
            "",
            "Average error inside the edited chat message compared with the other messages "
            "(synthetic sample, so the edit location is known).",
            "",
            "| Image | Edited message | Other messages (avg) | Other messages (max) | Ratio |",
            "|---|---|---|---|---|",
            *
            [
                f"| {
                    c['image']} | {
                    c['edited_message_error']:.3f} | {
                    c['other_messages_avg_error']:.3f} | " f"{
                        c['other_messages_max_error']:.3f} | {
                            c['ratio']:.2f}x |" for c in check],
            "",
        ]
    md += ["## How to read this",
           "",
           "- In the edited JPEG, the replaced message was compressed once "
           "while the rest was compressed twice, "
           "so it changes more on re-save and stands out in the heatmap.",
           "- In the unedited JPEG, that message behaves like the other messages.",
           "- Header, icons and coloured areas glow in every image: "
           "sharp edges and colour always produce more error.",
           "- The PNG screenshot has no compression history, so ELA there mostly shows edges.",
           "- ELA points a person at areas to check; it is not proof that an image was edited.",
           "",
           ]
    (RESULTS / "ela_report.md").write_text("\n".join(md), encoding="utf-8")
    print("\nSaved forensics_results/ela_report.md, .json and the panels in forensics_results/ela/")


if __name__ == "__main__":
    main()
