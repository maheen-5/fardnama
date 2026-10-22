"""Shared helpers for the FardNama dataset loaders.

Every loader turns one raw source into the same interim format:

    text, original_text, label, original_label, language, source, raw_file

Rules (labels, priority, AMBIGUOUS tag, source metadata) come from
config/taxonomy.yaml; per-source label mappings come from mappings/<source>.csv.
Nothing about labels is hard-coded here.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

COLUMNS = ["text", "original_text", "label", "original_label", "language", "source", "raw_file"]

_URL = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
_MENTION = re.compile(r"@\w+")
_SPACE = re.compile(r"\s+")


def load_taxonomy() -> dict:
    with open(ROOT / "config" / "taxonomy.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def allowed_labels(tax: dict | None = None) -> set[str]:
    tax = tax or load_taxonomy()
    return {str(l["id"]) for l in tax["labels"]} | {tax["ambiguous"]["tag"]}


def source_meta(source_id: str, tax: dict | None = None) -> dict:
    tax = tax or load_taxonomy()
    for s in tax["sources"]:
        if s["id"] == source_id:
            return s
    raise KeyError(f"{source_id} is not listed under sources in taxonomy.yaml")


def load_mapping(source_id: str, tax: dict | None = None) -> dict[str, str]:
    """original_label -> target_label, checked against taxonomy.yaml."""
    tax = tax or load_taxonomy()
    path = ROOT / source_meta(source_id, tax)["mapping_file"]
    ok = allowed_labels(tax)
    mapping: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            target = row["target_label"].strip()
            if target not in ok:
                raise ValueError(f"{path.name}: '{target}' is not a label in taxonomy.yaml")
            mapping[row["original_label"].strip()] = target
    return mapping


def pick_label(labels, tax: dict | None = None) -> str:
    """Single-label rule: the most severe label present, by taxonomy priority."""
    tax = tax or load_taxonomy()
    for lbl in tax["priority"]:
        if lbl in labels:
            return lbl
    return tax["ambiguous"]["tag"]


def normalize_text(s) -> str:
    """Light cleaning only: NFKC, URL/@mention placeholders, collapse whitespace.
    Case is kept (Urdu has none, and Roman Urdu casing can carry tone)."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = _URL.sub("<URL>", s)
    s = _MENTION.sub("<USER>", s)
    return _SPACE.sub(" ", s).strip()


def build_interim(df: pd.DataFrame, source_id: str) -> tuple[pd.DataFrame, dict]:
    """df needs columns: original_text, original_label, raw_file.
    Returns the interim frame and a log of what was removed and why."""
    tax = load_taxonomy()
    meta = source_meta(source_id, tax)
    mapping = load_mapping(source_id, tax)
    log = {"source": source_id, "rows_read": int(len(df))}

    df = df.copy()
    df["original_label"] = df["original_label"].astype(str).str.strip()
    unknown = sorted(set(df["original_label"]) - set(mapping))
    if unknown:
        raise ValueError(f"{source_id}: labels {unknown} are missing from {meta['mapping_file']}")

    df["text"] = df["original_text"].map(normalize_text)
    empty = df["text"].eq("")
    log["dropped_empty_text"] = int(empty.sum())
    df = df[~empty]

    df["label"] = df["original_label"].map(mapping)
    df["language"] = meta.get("language", "unknown")
    df["source"] = source_id

    # Within-source dedupe on the cleaned text.
    # Same text + same original label -> keep one. Same text, different labels -> drop all copies.
    before = len(df)
    df = df.drop_duplicates(subset=["text", "original_label"])
    log["dropped_exact_duplicates"] = int(before - len(df))
    n_labels = df.groupby("text")["original_label"].transform("nunique")
    conflict = n_labels > 1
    log["dropped_conflicting_texts"] = int(df.loc[conflict, "text"].nunique())
    log["dropped_conflicting_rows"] = int(conflict.sum())
    df = df[~conflict]

    df = df[COLUMNS].reset_index(drop=True)
    log["rows_out"] = int(len(df))
    log["label_counts"] = {k: int(v) for k, v in df["label"].value_counts().items()}
    log["original_label_counts"] = {k: int(v) for k, v in df["original_label"].value_counts().items()}
    return df, log


def write_interim(df: pd.DataFrame, log: dict) -> Path:
    INTERIM.mkdir(parents=True, exist_ok=True)
    out = INTERIM / f"{log['source']}.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    with open(INTERIM / f"{log['source']}_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    return out


def report(log: dict) -> None:
    print(f"\n== {log['source']} ==")
    for k in ["rows_read", "dropped_empty_text", "dropped_exact_duplicates",
              "dropped_conflicting_texts", "dropped_conflicting_rows", "rows_out"]:
        print(f"  {k:28s} {log[k]}")
    print("  labels:", log["label_counts"])
    for w in log.get("warnings", []):
        print("  WARNING:", w)
