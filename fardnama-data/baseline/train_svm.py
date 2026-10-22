"""SVM + TF-IDF baseline classifier for FardNama (FYP-1 Mid baseline).

What it does
  1. Reads data/processed/v1/{train,val,test}.csv (+ hard_negatives.csv).
  2. Turns text into TF-IDF features: word 1-2 grams + character 2-5 grams
     (character n-grams help with Roman Urdu spelling variation: kutta / kutya / kuttay).
  3. Trains a linear SVM with class_weight="balanced" (Threat has only ~71 training rows).
  4. Picks the SVM setting C on the validation set (best macro-F1).
  5. Evaluates ONCE on the test set: per-class precision/recall/F1, macro-F1, confusion matrix,
     per language, per source, and the false-alarm rate on the hard-negative set.
  6. Saves the model and a Markdown + JSON report.

It runs two configurations by default (the taxonomy asks for both):
  all    - every source
  no_s1  - without s1_roman_urdu_abuse (suspected synthetic)

Usage (from the project root):
  python baseline/train_svm.py                 # both configurations
  python baseline/train_svm.py --configs all   # only one
Outputs:
  models/svm_v1_<config>.joblib
  results/svm_v1_<config>.md   and   results/svm_v1_<config>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harmonize"))
from common import load_taxonomy  # noqa: E402

CONFIGS = {
    "all": [],
    "no_s1": ["s1_roman_urdu_abuse"],
}
C_GRID = [0.1, 0.3, 1.0, 3.0]


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def build_pipeline(C: float = 1.0, small: bool = False) -> Pipeline:
    """small=True drops the min_df limits so the unit tests can run on a few rows."""
    min_word, min_char = (1, 1) if small else (2, 3)
    features = FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=min_word,
                                 sublinear_tf=True, max_features=200_000)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=min_char,
                                 sublinear_tf=True, max_features=300_000)),
    ])
    return Pipeline([
        ("tfidf", features),
        ("svm", LinearSVC(C=C, class_weight="balanced", max_iter=5000)),
    ])


def group_scores(df: pd.DataFrame, pred: np.ndarray, by: str, labels: list[str]) -> dict:
    out = {}
    for key, idx in df.groupby(by).groups.items():
        y, p = df.loc[idx, "label"], pred[df.index.get_indexer(idx)]
        present = [l for l in labels if l in set(y)]
        out[str(key)] = {
            "rows": int(len(idx)),
            "macro_f1": round(float(f1_score(y, p, labels=present, average="macro", zero_division=0)), 4),
            "per_class": classification_report(y, p, labels=present, output_dict=True, zero_division=0),
        }
    return out


def top_features(model: Pipeline, n: int = 15) -> dict:
    names = model.named_steps["tfidf"].get_feature_names_out()
    svm = model.named_steps["svm"]
    coef = svm.coef_
    if coef.shape[0] == 1:  # binary case: one row of weights
        coef = np.vstack([-coef[0], coef[0]])
    return {str(c): [names[i] for i in np.argsort(coef[k])[::-1][:n]] for k, c in enumerate(svm.classes_)}


def run_config(name: str, exclude: list[str], data_dir: Path, version: str) -> dict:
    tax = load_taxonomy()
    order = [str(l["id"]) for l in tax["labels"]]

    def load(split):
        df = read(data_dir / f"{split}.csv")
        return df[~df["source"].isin(exclude)].reset_index(drop=True)

    train, val, test = load("train"), load("val"), load("test")
    labels = [l for l in order if l in set(train["label"])]
    print(f"\n=== config '{name}': train {len(train):,} / val {len(val):,} / test {len(test):,} ===")
    print("labels:", labels)

    # 1) choose C on the validation set
    tuning = []
    for C in C_GRID:
        t0 = time.time()
        m = build_pipeline(C).fit(train["text"], train["label"])
        f1 = f1_score(val["label"], m.predict(val["text"]), labels=labels, average="macro", zero_division=0)
        tuning.append({"C": C, "val_macro_f1": round(float(f1), 4), "seconds": round(time.time() - t0, 1)})
        print(f"  C={C:<4} val macro-F1={f1:.4f}  ({tuning[-1]['seconds']}s)")
    best_C = max(tuning, key=lambda r: r["val_macro_f1"])["C"]
    print(f"  best C = {best_C}")

    # 2) final model on train with the best C, evaluated once on test
    model = build_pipeline(best_C).fit(train["text"], train["label"])
    pred = model.predict(test["text"])
    result = {
        "config": name,
        "dataset": version,
        "excluded_sources": exclude,
        "rows": {"train": len(train), "val": len(val), "test": len(test)},
        "labels": labels,
        "tuning": tuning,
        "best_C": best_C,
        "test_macro_f1": round(float(f1_score(test["label"], pred, labels=labels, average="macro", zero_division=0)), 4),
        "test_report": classification_report(test["label"], pred, labels=labels, output_dict=True, zero_division=0),
        "confusion_matrix": {"labels": labels, "matrix": confusion_matrix(test["label"], pred, labels=labels).tolist()},
        "by_language": group_scores(test, pred, "language", labels),
        "by_source": group_scores(test, pred, "source", labels),
        "top_features": top_features(model),
    }

    # 3) hard negatives: casual profanity that should NOT be flagged
    hn_path = data_dir / "hard_negatives.csv"
    if hn_path.exists():
        hn = read(hn_path)
        hp = model.predict(hn["text"])
        flagged = pd.Series(hp).value_counts().to_dict()
        result["hard_negatives"] = {
            "rows": int(len(hn)),
            "predicted": {str(k): int(v) for k, v in flagged.items()},
            "false_alarm_rate": round(float(np.mean(hp != "Neutral")), 4),
        }

    models_dir, results_dir = ROOT / "models", ROOT / "results"
    models_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    stem = f"svm_{version}_{name}"
    joblib.dump(model, models_dir / f"{stem}.joblib")
    (results_dir / f"{stem}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (results_dir / f"{stem}.md").write_text(to_markdown(result), encoding="utf-8")
    print(f"  test macro-F1 = {result['test_macro_f1']}  ->  results/{stem}.md")
    return result


def to_markdown(r: dict) -> str:
    L = r["labels"]
    rep = r["test_report"]
    md = [
        f"# SVM + TF-IDF baseline — dataset {r['dataset']}, config `{r['config']}`",
        "",
        f"Excluded sources: {', '.join(r['excluded_sources']) or 'none'}. "
        f"Rows: train {r['rows']['train']:,}, val {r['rows']['val']:,}, test {r['rows']['test']:,}.",
        f"Features: word 1-2 grams + char 2-5 grams (TF-IDF). Model: LinearSVC, class_weight=balanced, C={r['best_C']} (chosen on val).",
        "",
        f"## Test macro-F1: **{r['test_macro_f1']}**",
        "",
        "| Class | Precision | Recall | F1 | Test rows |",
        "|---|---|---|---|---|",
        *[f"| {c} | {rep[c]['precision']:.3f} | {rep[c]['recall']:.3f} | {rep[c]['f1-score']:.3f} | {int(rep[c]['support']):,} |" for c in L],
        "",
        "## Confusion matrix (rows = true, columns = predicted)",
        "",
        "| true \\ pred | " + " | ".join(L) + " |",
        "|---" * (len(L) + 1) + "|",
        *[f"| {L[i]} | " + " | ".join(f"{v:,}" for v in row) + " |" for i, row in enumerate(r["confusion_matrix"]["matrix"])],
        "",
        "## By language",
        "",
        "| Language | Test rows | Macro-F1 | " + " | ".join(f"{c} recall" for c in L) + " |",
        "|---" * (len(L) + 3) + "|",
    ]
    for lang, g in r["by_language"].items():
        rec = [f"{g['per_class'][c]['recall']:.3f}" if c in g["per_class"] else "–" for c in L]
        md.append(f"| {lang} | {g['rows']:,} | {g['macro_f1']} | " + " | ".join(rec) + " |")
    md += ["", "## By source", "", "| Source | Test rows | Macro-F1 |", "|---|---|---|"]
    md += [f"| {s} | {g['rows']:,} | {g['macro_f1']} |" for s, g in r["by_source"].items()]
    if "hard_negatives" in r:
        h = r["hard_negatives"]
        md += ["", "## Hard negatives (casual profanity, should stay Neutral)", "",
               f"{h['rows']:,} rows. False-alarm rate: **{h['false_alarm_rate']:.1%}**. Predicted: {h['predicted']}"]
    md += ["", "## C tuning on validation", "", "| C | Val macro-F1 | Seconds |", "|---|---|---|"]
    md += [f"| {t['C']} | {t['val_macro_f1']} | {t['seconds']} |" for t in r["tuning"]]
    md += ["", "## Top features per class (what the model relies on)", ""]
    md += [f"- **{c}**: {', '.join(f'`{w}`' for w in ws)}" for c, ws in r["top_features"].items()]
    md += ["", "## Notes for the report", "",
           "- Threat has very few test rows, so its recall moves a lot with each prediction.",
           "- Hate speech exists only in Roman Urdu and Threat only in Urdu script: check the by-language table "
           "and the top features for a language shortcut instead of real meaning.", ""]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", nargs="+", default=list(CONFIGS), choices=list(CONFIGS))
    args = ap.parse_args()
    tax = load_taxonomy()
    version = f"v{tax['version']}"
    data_dir = ROOT / "data" / "processed" / version
    summary = {name: run_config(name, CONFIGS[name], data_dir, version)["test_macro_f1"] for name in args.configs}
    print("\nSummary (test macro-F1):", summary)


if __name__ == "__main__":
    main()
