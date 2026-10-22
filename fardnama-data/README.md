# FardNama dataset harmonization

Turns the downloaded cyberbullying datasets into one labelled dataset that follows
`config/taxonomy.yaml` (owner: M. Noor Ul Azeem).

## Layout

```
config/taxonomy.yaml        labels, priority order, AMBIGUOUS rule, source list
mappings/<source>.csv       original label -> target label, one file per source
data/raw/<source>/          downloaded files, never edited
data/interim/<source>.csv   one source in the common format (made by the loaders)
data/processed/v1/          train / val / test (next step: merge + split)
harmonize/                  loader scripts
tests/                      pytest checks for the config and mappings
```

## Run

```
pip install -r requirements.txt
python harmonize/run_all.py     # writes data/interim/*.csv and *_log.json
pytest                          # checks taxonomy + mappings
```

Each loader writes `data/interim/<source>.csv` with the columns
`text, original_text, label, original_label, language, source, raw_file`,
and a `<source>_log.json` that records how many rows were dropped and why
(empty text, exact duplicates, texts with conflicting labels).

## Known data issues

- `data/raw/s5_rizwan/task_2_validation.tsv` is a byte-for-byte copy of `task_2_train.tsv`.
  This is how the authors' repo ships it (github.com/haroonshakeel/roman_urdu_hate_speech,
  checked 2026-10-18: both files have 7,209 lines), so no separate validation set exists.
  The loader skips the copy. Source 5 = task_2_train + task_2_test, deduplicated.
- Source 4 text is already preprocessed by its authors (stopwords removed, lemmatized).
- Source 1 may be synthetic (unconfirmed); report results with and without it.

## Merge and split

```
python harmonize/merge_split.py   # writes data/processed/v1/
```

Cross-source dedupe (most severe label wins on conflicts), hard negatives and AMBIGUOUS rows held out,
then an 80/10/10 split stratified on label + language with the seed from `config/taxonomy.yaml`.
Outputs: `train.csv`, `val.csv`, `test.csv`, `ambiguous.csv`, `hard_negatives.csv`, `stats.md`, `manifest.json`.
Read them with `dtype=str, keep_default_na=False`.

## SVM + TF-IDF baseline

```
python baseline/train_svm.py                 # both configs: all sources, and without s1
python baseline/train_svm.py --configs all   # one config only
```

Word 1-2 grams + char 2-5 grams (TF-IDF), LinearSVC with class_weight=balanced, C chosen on val,
evaluated once on test. Writes `models/svm_v1_<config>.joblib` and `results/svm_v1_<config>.md` / `.json`
(per-class scores, confusion matrix, per language, per source, hard-negative false-alarm rate,
top features per class).

## Data sources and licences

Raw data is not stored in this repository. Download each source into data/raw/<folder>/:

| Folder              | Source                                                                                                                                       | Licence                         |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|
| s1_roman_urdu_abuse | Roman Urdu Cyber Abuse Dataset, Kaggle (hassan7838): kaggle.com/datasets/hassan7838/roman-urdu-cyber-abuse-dataset                           | CC BY-SA 4.0                    |
| s3_wiki_aggression  | Cyberbullying Dataset, Kaggle (saurabhshahane), file aggression_parsed_dataset.csv: kaggle.com/datasets/saurabhshahane/cyberbullying-dataset | CC BY-SA 4.0                    |
| s4_farah_zenodo     | Farah (2024), Cyberbullying Data, Zenodo: doi.org/10.5281/zenodo.10581022                                                                    | CC BY 4.0                       |
| s5_rizwan           | Rizwan, Shakeel & Karim (2020), Task 2 files: github.com/haroonshakeel/roman_urdu_hate_speech                                                | MIT, (c) 2020 M. Haroon Shakeel |

Data and trained models are rebuilt by the scripts and are not redistributed here.