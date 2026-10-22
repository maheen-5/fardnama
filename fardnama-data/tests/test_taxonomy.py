"""Checks that the taxonomy config, the mapping CSVs and the shared helpers agree.
Run from the project root:  pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harmonize"))

import pytest  # noqa: E402

from common import (ROOT, allowed_labels, load_mapping, load_taxonomy,  # noqa: E402
                    normalize_text, pick_label)

TAX = load_taxonomy()
USED = [s["id"] for s in TAX["sources"] if s["status"] == "used"]


def test_priority_covers_every_label_once():
    ids = [str(l["id"]) for l in TAX["labels"]]
    assert sorted(ids) == sorted(TAX["priority"])
    assert len(set(TAX["priority"])) == len(TAX["priority"])


@pytest.mark.parametrize("source_id", USED)
def test_mapping_file_exists_and_targets_are_valid(source_id):
    mapping = load_mapping(source_id, TAX)  # raises on an unknown target label
    assert mapping, f"{source_id} mapping is empty"
    assert set(mapping.values()) <= allowed_labels(TAX)


def test_known_mappings_match_the_taxonomy_document():
    assert load_mapping("s4_farah_zenodo")["THREAT"] == "Threat"
    assert load_mapping("s4_farah_zenodo")["CURSE"] == TAX["ambiguous"]["tag"]
    s5 = load_mapping("s5_rizwan")
    assert s5["2"] == s5["3"] == "Hate_speech"
    assert s5["4"] == TAX["ambiguous"]["tag"]


@pytest.mark.parametrize("labels, expected", [
    ({"Threat", "Hate_speech"}, "Threat"),
    ({"Harassment", "Hate_speech"}, "Hate_speech"),
    ({"Doxxing", "Harassment"}, "Doxxing"),
    ({"Neutral"}, "Neutral"),
    (set(), "AMBIGUOUS"),
])
def test_pick_label_uses_priority(labels, expected):
    assert pick_label(labels, TAX) == expected


def test_normalize_text():
    assert normalize_text("  Aray   yaar\n bro ") == "Aray yaar bro"
    assert normalize_text("dekho https://x.com/a @ali") == "dekho <URL> <USER>"
    assert normalize_text(None) == ""
    assert normalize_text("Ｆｕｌｌ") == "Full"  # NFKC folds full-width letters


def test_ambiguous_rows_are_excluded_from_training():
    assert TAX["ambiguous"]["use_in_training"] is False
    assert (ROOT / "config" / "taxonomy.yaml").exists()
