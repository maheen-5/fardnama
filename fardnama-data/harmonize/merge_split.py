"""Merge the per-source interim files into one dataset and make the train/val/test split.

Steps
  1. Read data/interim/<source>.csv for every source marked `used` in taxonomy.yaml.
  2. Cross-source dedupe on the cleaned text. If the copies carry different labels,
     the most severe one wins (taxonomy priority), as the taxonomy document says.
  3. Hold out the hard-negative set(s) named in taxonomy.yaml (Source 5, label 4).
  4. Hold out the remaining AMBIGUOUS rows (not used for training).
  5. Stratified split on label + language with the ratios and seed from taxonomy.yaml.
  6. Write data/processed/v<version>/ : train.csv, val.csv, test.csv,
     ambiguous.csv, hard_negatives.csv, stats.md, manifest.json.

Usage (from the project root):  python harmonize/merge_split.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import INTERIM, ROOT, load_taxonomy, pick_label  # noqa: E402


def read_interim(source_id: str) -> pd.DataFrame:
    return pd.read_csv(INTERIM / f"{source_id}.csv", dtype=str, keep_default_na=False, encoding="utf-8")


def cross_source_dedupe(df: pd.DataFrame, tax: dict) -> tuple[pd.DataFrame, dict]:
    """One row per text. Agreeing copies keep the first; conflicting copies take the most severe label."""
    log = {"rows_in": int(len(df))}
    groups = df.groupby("text", sort=False)
    n_sources = groups["source"].transform("nunique")
    n_labels = groups["label"].transform("nunique")
    log["texts_in_more_than_one_source"] = int(df.loc[n_sources > 1, "text"].nunique())
    log["texts_with_conflicting_labels"] = int(df.loc[n_labels > 1, "text"].nunique())

    winner = groups["label"].agg(lambda s: pick_label(set(s), tax))
    df = df.assign(_winner=df["text"].map(winner))
    df = df[df["label"] == df["_winner"]].drop_duplicates(subset=["text"]).drop(columns="_winner")
    df = df.assign(n_sources=df["text"].map(groups["source"].nunique()))
    log["rows_out"] = int(len(df))
    log["rows_removed"] = log["rows_in"] - log["rows_out"]
    return df.reset_index(drop=True), log


def stratified_split(df: pd.DataFrame, keys: list[str], ratios: dict, seed: int) -> pd.Series:
    """Deterministic per-stratum split. Returns a Series of 'train' / 'val' / 'test'.
    Each stratum (e.g. Threat + urdu_script) is shuffled with the seed and cut by the ratios,
    so even small classes get rows in val and test whenever the stratum has 3 or more rows."""
    rng = random.Random(seed)
    split = pd.Series("train", index=df.index)
    for _, idx in sorted(df.groupby(keys).groups.items(), key=lambda kv: str(kv[0])):
        idx = sorted(idx)
        rng.shuffle(idx)
        n = len(idx)
        n_test = round(n * ratios["test"])
        n_val = round(n * ratios["val"])
        if n >= 3:
            n_test, n_val = max(n_test, 1), max(n_val, 1)
        split.loc[idx[:n_test]] = "test"
        split.loc[idx[n_test:n_test + n_val]] = "val"
    return split


def crosstab_md(df: pd.DataFrame, rows: str, cols: str) -> str:
    t = pd.crosstab(df[rows], df[cols], margins=True, margins_name="Total")
    head = "| " + rows + " | " + " | ".join(map(str, t.columns)) + " |"
    sep = "|" + "---|" * (len(t.columns) + 1)
    body = ["| " + str(i) + " | " + " | ".join(f"{v:,}" for v in r) + " |" for i, r in t.iterrows()]
    return "\n".join([head, sep, *body])


def main():
    tax = load_taxonomy()
    out_dir = ROOT / "data" / "processed" / f"v{tax['version']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    used = [s["id"] for s in tax["sources"] if s["status"] == "used"]

    df = pd.concat([read_interim(s) for s in used], ignore_index=True)
    df, dedupe_log = cross_source_dedupe(df, tax)

    # Hard negatives first (they are also AMBIGUOUS), then the remaining AMBIGUOUS rows.
    is_hard = pd.Series(False, index=df.index)
    for hn in tax.get("hard_negative_sets", []):
        is_hard |= (df["source"] == hn["source"]) & df["original_label"].isin([str(x) for x in hn["original_labels"]])
    hard = df[is_hard]
    rest = df[~is_hard]
    amb_tag = tax["ambiguous"]["tag"]
    ambiguous = rest[rest["label"] == amb_tag]
    pool = rest[rest["label"] != amb_tag].copy()

    cfg = tax["baseline"]["split"]
    pool["split"] = stratified_split(pool, cfg["stratify_on"], cfg["ratios"], cfg["seed"])

    # Leakage check: no text may sit in two splits.
    assert pool.groupby("text")["split"].nunique().max() == 1, "a text appears in more than one split"

    files = {}
    for name in ["train", "val", "test"]:
        part = pool[pool["split"] == name].drop(columns="split")
        part.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8")
        files[name] = int(len(part))
    ambiguous.to_csv(out_dir / "ambiguous.csv", index=False, encoding="utf-8")
    hard.to_csv(out_dir / "hard_negatives.csv", index=False, encoding="utf-8")
    files["ambiguous"] = int(len(ambiguous))
    files["hard_negatives"] = int(len(hard))

    manifest = {
        "dataset_version": f"v{tax['version']}",
        "sources": used,
        "seed": cfg["seed"],
        "ratios": cfg["ratios"],
        "stratify_on": cfg["stratify_on"],
        "cross_source_dedupe": dedupe_log,
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    split_order = pd.CategoricalDtype(["train", "val", "test"], ordered=True)
    pool["split"] = pool["split"].astype(split_order)
    md = [
        f"# FardNama dataset {manifest['dataset_version']} — stats",
        "",
        f"Made by `harmonize/merge_split.py` from {', '.join(used)}. "
        f"Split {cfg['ratios']['train']:.0%} / {cfg['ratios']['val']:.0%} / {cfg['ratios']['test']:.0%}, "
        f"stratified on {' + '.join(cfg['stratify_on'])}, seed {cfg['seed']}.",
        "",
        "## Row flow",
        "",
        "| Step | Rows |",
        "|---|---|",
        f"| Interim rows (after within-source cleaning) | {dedupe_log['rows_in']:,} |",
        f"| Removed as cross-source duplicates | {dedupe_log['rows_removed']:,} |",
        f"| Texts found in more than one source | {dedupe_log['texts_in_more_than_one_source']:,} |",
        f"| ...of which had conflicting labels (most severe kept) | {dedupe_log['texts_with_conflicting_labels']:,} |",
        f"| Held out: hard negatives | {files['hard_negatives']:,} |",
        f"| Held out: AMBIGUOUS | {files['ambiguous']:,} |",
        f"| Train | {files['train']:,} |",
        f"| Val | {files['val']:,} |",
        f"| Test | {files['test']:,} |",
        "",
        "## Label × split", "", crosstab_md(pool, "label", "split"), "",
        "## Label × language (all splits)", "", crosstab_md(pool, "label", "language"), "",
        "## Language × split", "", crosstab_md(pool, "language", "split"), "",
        "## Source × split", "", crosstab_md(pool, "source", "split"), "",
        "## Notes", "",
        "- Doxxing has no rows in any source, so it does not appear in these tables.",
        "- English (Source 3) dominates; report baseline results per language and per source.",
        "- Report results with and without s1_roman_urdu_abuse (suspected synthetic).",
        "- Read these CSVs with dtype=str and keep_default_na=False to be safe.",
        "",
    ]
    (out_dir / "stats.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Wrote {out_dir}")
    for k, v in files.items():
        print(f"  {k:15s} {v:>8,}")
    print("  cross-source:", dedupe_log)


if __name__ == "__main__":
    main()
