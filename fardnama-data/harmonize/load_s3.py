"""Source 3: Wikipedia aggression (Kaggle, saurabhshahane), aggression_parsed_dataset.csv.
Columns: index, Text, ed_label_0, ed_label_1, oh_label. oh_label is already 0/1, so no vote is needed."""
import pandas as pd

from common import RAW, build_interim, report, write_interim

SOURCE = "s3_wiki_aggression"
FILE = RAW / SOURCE / "aggression_parsed_dataset.csv"


def main():
    raw = pd.read_csv(FILE, encoding="utf-8")
    df = pd.DataFrame({
        "original_text": raw["Text"],
        "original_label": raw["oh_label"],
        "raw_file": FILE.name,
    })
    df, log = build_interim(df, SOURCE)
    write_interim(df, log)
    report(log)


if __name__ == "__main__":
    main()
