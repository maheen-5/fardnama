"""Run every source loader, then print one summary table.
Usage (from the project root):  python harmonize/run_all.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import load_s1, load_s3, load_s4, load_s5  # noqa: E402
from common import INTERIM  # noqa: E402

LOADERS = [load_s1, load_s3, load_s4, load_s5]


def main():
    for loader in LOADERS:
        loader.main()

    print("\n== Summary (after within-source cleaning) ==")
    total = {}
    for loader in LOADERS:
        log = json.loads((INTERIM / f"{loader.SOURCE}_log.json").read_text(encoding="utf-8"))
        print(f"  {loader.SOURCE:22s} {log['rows_out']:>8,} rows")
        for k, v in log["label_counts"].items():
            total[k] = total.get(k, 0) + v
    n = sum(total.values())
    print(f"  {'TOTAL':22s} {n:>8,} rows")
    for k, v in sorted(total.items(), key=lambda kv: -kv[1]):
        print(f"    {k:12s} {v:>8,}  {v / n:6.2%}")


if __name__ == "__main__":
    main()
