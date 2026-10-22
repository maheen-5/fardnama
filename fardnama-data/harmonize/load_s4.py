"""Source 4: Farah (2024) Cyberbullying Data, Zenodo. Two XLSX files, columns: Unnamed: 0, preprocessed_text, LABEL.
The authors' train/test split is ignored (we make our own); raw_file keeps where each row came from.
Texts that appear in both files are removed as duplicates by build_interim."""
import pandas as pd

from common import RAW, build_interim, report, write_interim

SOURCE = "s4_farah_zenodo"
FILES = [RAW / SOURCE / "train_bullying.xlsx", RAW / SOURCE / "test_bullying.xlsx"]


def main():
    parts = []
    for f in FILES:
        raw = pd.read_excel(f)
        parts.append(pd.DataFrame({
            "original_text": raw["preprocessed_text"],
            "original_label": raw["LABEL"],
            "raw_file": f.name,
        }))
    df = pd.concat(parts, ignore_index=True)
    df, log = build_interim(df, SOURCE)
    log["warnings"] = ["Text is already preprocessed by the authors (stopwords removed, lemmatized)."]
    write_interim(df, log)
    report(log)


if __name__ == "__main__":
    main()
