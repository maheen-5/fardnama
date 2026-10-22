"""Source 1: Roman Urdu Cyber Abuse Dataset (Kaggle, hassan7838). CSV: id, comment, label (H/O)."""
import pandas as pd

from common import RAW, build_interim, report, write_interim

SOURCE = "s1_roman_urdu_abuse"
FILE = RAW / SOURCE / "roman_urdu_cyber_abuse_dataset.csv"


def main():
    raw = pd.read_csv(FILE, encoding="utf-8")
    df = pd.DataFrame({
        "original_text": raw["comment"],
        "original_label": raw["label"],
        "raw_file": FILE.name,
    })
    df, log = build_interim(df, SOURCE)
    write_interim(df, log)
    report(log)


if __name__ == "__main__":
    main()
