# SVM + TF-IDF baseline — dataset v1, config `all`

Excluded sources: none. Rows: train 111,884, val 13,986, test 13,986.
Features: word 1-2 grams + char 2-5 grams (TF-IDF). Model: LinearSVC, class_weight=balanced, C=3.0 (chosen on val).

## Test macro-F1: **0.7729**

| Class | Precision | Recall | F1 | Test rows |
|---|---|---|---|---|
| Threat | 1.000 | 0.444 | 0.615 | 9 |
| Hate_speech | 0.797 | 0.685 | 0.736 | 149 |
| Harassment | 0.802 | 0.761 | 0.781 | 2,268 |
| Neutral | 0.953 | 0.964 | 0.958 | 11,560 |

## Confusion matrix (rows = true, columns = predicted)

| true \ pred | Threat | Hate_speech | Harassment | Neutral |
|---|---|---|---|---|
| Threat | 4 | 0 | 3 | 2 |
| Hate_speech | 0 | 102 | 24 | 23 |
| Harassment | 0 | 12 | 1,727 | 529 |
| Neutral | 0 | 14 | 399 | 11,147 |

## By language

| Language | Test rows | Macro-F1 | Threat recall | Hate_speech recall | Harassment recall | Neutral recall |
|---|---|---|---|---|---|---|
| english | 11,528 | 0.8581 | – | – | 0.717 | 0.972 |
| roman_urdu | 1,319 | 0.8464 | – | 0.685 | 0.879 | 0.936 |
| urdu_script | 1,139 | 0.7648 | 0.444 | – | 0.794 | 0.896 |

## By source

| Source | Test rows | Macro-F1 |
|---|---|---|
| s1_roman_urdu_abuse | 472 | 1.0 |
| s3_wiki_aggression | 11,528 | 0.8581 |
| s4_farah_zenodo | 1,139 | 0.7648 |
| s5_rizwan | 847 | 0.7874 |

## Hard negatives (casual profanity, should stay Neutral)

582 rows. False-alarm rate: **75.3%**. Predicted: {'Harassment': 405, 'Neutral': 144, 'Hate_speech': 33}

## C tuning on validation

| C | Val macro-F1 | Seconds |
|---|---|---|
| 0.1 | 0.7197 | 299.7 |
| 0.3 | 0.7404 | 333.8 |
| 1.0 | 0.7404 | 246.5 |
| 3.0 | 0.7407 | 270.4 |

## Top features per class (what the model relies on)

- **Harassment**: `char__uck`, `word__لن`, `char__fuc`, `word__ass`, `char__fuck`, `word__امپورٹڈ حکومت`, `word__شاپر`, `word__please bhadwi`, `word__نکما`, `word__bc`, `word__idiot`, `word__کمینہ`, `word__fuck`, `word__you`, `word__bahanchod`
- **Hate_speech**: `word__halala`, `word__khusray`, `word__yahodi`, `word__athiest`, `word__yahoodi`, `char__ rand`, `word__randi`, `word__kanjeri`, `word__hijra`, `word__halala ki`, `char__ hij`, `char__ ran`, `word__ghasti`, `word__kanjari`, `char__hij`
- **Neutral**: `word__you pussy`, `word__eat shit`, `word__کسان`, `word__re little`, `word__my dick`, `word__are cunt`, `word__فون`, `word__marchagainstimportedgovt امپورٹڈ`, `word__trans`, `word__پاکستان بڑا`, `word__is now`, `word__am sorry`, `word__dick you`, `word__you hate`, `word__fat cunt`
- **Threat**: `word__باعزت`, `word__تمہ`, `word__تمہ قتل`, `word__نہ ھو`, `word__گی`, `word__رکھنا دینا`, `word__آنکھ نکلنا`, `word__اگر عمران`, `word__لات`, `word__نکلنا دینا`, `word__استعفی دو`, `word__بعض`, `word__فرار`, `word__خان ایک`, `word__جانا سکنا`

## Notes for the report

- Threat has very few test rows, so its recall moves a lot with each prediction.
- Hate speech exists only in Roman Urdu and Threat only in Urdu script: check the by-language table and the top features for a language shortcut instead of real meaning.
