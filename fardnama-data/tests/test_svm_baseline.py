"""Small checks for the SVM baseline on made-up data (fast; no real dataset needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "baseline"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from train_svm import build_pipeline, group_scores, top_features  # noqa: E402

TEXTS = ["tujhe maar dunga", "main tujhe maar dalunga", "ghar aa ke maar dunga",
         "shukriya bhai", "bohat acha video", "mashallah zabardast",
         "tu pagal hai", "bewaqoof insaan", "tu bilkul pagal"]
LABELS = ["Threat"] * 3 + ["Neutral"] * 3 + ["Harassment"] * 3


def test_pipeline_learns_a_tiny_dataset():
    model = build_pipeline(C=1.0, small=True).fit(TEXTS, LABELS)
    assert list(model.predict(["maar dunga tujhe", "shukriya zabardast video"])) == ["Threat", "Neutral"]


def test_top_features_has_one_list_per_class():
    model = build_pipeline(C=1.0, small=True).fit(TEXTS, LABELS)
    feats = top_features(model, n=5)
    assert set(feats) == set(LABELS)
    assert all(len(v) == 5 for v in feats.values())


def test_group_scores_per_language():
    df = pd.DataFrame({"label": ["Threat", "Neutral", "Neutral", "Threat"],
                       "language": ["urdu_script", "english", "english", "urdu_script"]})
    pred = np.array(["Threat", "Neutral", "Threat", "Threat"])
    out = group_scores(df, pred, "language", ["Threat", "Neutral"])
    assert out["urdu_script"]["macro_f1"] == 1.0
    assert out["english"]["rows"] == 2
