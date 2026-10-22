"""Checks for the merge + split logic on small made-up data (no real dataset needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harmonize"))

import pandas as pd  # noqa: E402

from common import load_taxonomy  # noqa: E402
from merge_split import cross_source_dedupe, stratified_split  # noqa: E402

TAX = load_taxonomy()
RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}


def frame(rows):
    return pd.DataFrame(rows, columns=["text", "label", "source", "language", "original_label"])


def test_conflicting_copies_keep_the_most_severe_label():
    df = frame([
        ["same text", "Harassment", "s3", "english", "1"],
        ["same text", "Threat", "s4", "english", "THREAT"],
        ["other", "Neutral", "s3", "english", "0"],
    ])
    out, log = cross_source_dedupe(df, TAX)
    assert len(out) == 2
    assert out.set_index("text").loc["same text", "label"] == "Threat"
    assert log["texts_with_conflicting_labels"] == 1


def test_agreeing_copies_become_one_row():
    df = frame([
        ["dup", "Neutral", "s1", "roman_urdu", "O"],
        ["dup", "Neutral", "s5", "roman_urdu", "1"],
    ])
    out, log = cross_source_dedupe(df, TAX)
    assert len(out) == 1 and log["rows_removed"] == 1


def big_frame():
    rows = [[f"n{i}", "Neutral", "s3", "english", "0"] for i in range(200)]
    rows += [[f"t{i}", "Threat", "s4", "urdu_script", "THREAT"] for i in range(9)]
    return frame(rows)


def test_split_is_deterministic():
    df = big_frame()
    a = stratified_split(df, ["label", "language"], RATIOS, 42)
    b = stratified_split(df, ["label", "language"], RATIOS, 42)
    assert a.equals(b)


def test_split_ratios_and_small_class_reaches_val_and_test():
    df = big_frame()
    s = stratified_split(df, ["label", "language"], RATIOS, 42)
    neutral = s[df["label"] == "Neutral"].value_counts()
    assert neutral["train"] == 160 and neutral["val"] == 20 and neutral["test"] == 20
    threat = s[df["label"] == "Threat"].value_counts()
    assert threat.get("val", 0) >= 1 and threat.get("test", 0) >= 1
