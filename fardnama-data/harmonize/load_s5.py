"""Source 5: Rizwan, Shakeel & Karim (2020), Roman Urdu, Task 2 (fine-grained).
TSV files with no header: column 0 = text, column 1 = label (0-4). Task 1 files are not used.

Any file that is a byte-for-byte copy of another is skipped with a warning
(the authors' own repo ships task_2_validation.tsv as a copy of task_2_train.tsv,
checked on GitHub 2026-10-18: both have 7,209 lines, so no separate validation set exists)."""
import csv
import hashlib

import pandas as pd

from common import RAW, build_interim, report, write_interim

SOURCE = "s5_rizwan"
FILES = [RAW / SOURCE / n for n in ("task_2_train.tsv", "task_2_validation.tsv", "task_2_test.tsv")]


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def main():
    parts, seen, warnings = [], {}, []
    for f in FILES:
        if not f.exists():
            warnings.append(f"{f.name} not found, skipped.")
            continue
        h = md5(f)
        if h in seen:
            warnings.append(f"{f.name} is an exact copy of {seen[h]} (also in the authors' repo), skipped.")
            continue
        seen[h] = f.name
        raw = pd.read_csv(f, sep="\t", header=None, quoting=csv.QUOTE_NONE,
                          encoding="utf-8", dtype=str, keep_default_na=False)
        parts.append(pd.DataFrame({
            "original_text": raw[0],
            "original_label": raw[1],
            "raw_file": f.name,
        }))
    df = pd.concat(parts, ignore_index=True)
    df, log = build_interim(df, SOURCE)
    log["warnings"] = warnings
    write_interim(df, log)
    report(log)


if __name__ == "__main__":
    main()
