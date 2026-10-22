# SVM + TF-IDF baseline — dataset v1, config `no_s1`

Excluded sources: s1_roman_urdu_abuse. Rows: train 108,247, val 13,511, test 13,514.
Features: word 1-2 grams + char 2-5 grams (TF-IDF). Model: LinearSVC, class_weight=balanced, C=0.3 (chosen on val).

## Test macro-F1: **0.7621**

| Class | Precision | Recall | F1 | Test rows |
|---|---|---|---|---|
| Threat | 0.800 | 0.444 | 0.571 | 9 |
| Hate_speech | 0.735 | 0.765 | 0.750 | 149 |
| Harassment | 0.784 | 0.751 | 0.767 | 2,024 |
| Neutral | 0.956 | 0.963 | 0.960 | 11,332 |

## Confusion matrix (rows = true, columns = predicted)

| true \ pred | Threat | Hate_speech | Harassment | Neutral |
|---|---|---|---|---|
| Threat | 4 | 0 | 2 | 3 |
| Hate_speech | 0 | 114 | 23 | 12 |
| Harassment | 1 | 20 | 1,520 | 483 |
| Neutral | 0 | 21 | 394 | 10,917 |

## By language

| Language | Test rows | Macro-F1 | Threat recall | Hate_speech recall | Harassment recall | Neutral recall |
|---|---|---|---|---|---|---|
| english | 11,528 | 0.8695 | – | – | 0.745 | 0.973 |
| roman_urdu | 847 | 0.7932 | – | 0.765 | 0.714 | 0.902 |
| urdu_script | 1,139 | 0.7459 | 0.444 | – | 0.797 | 0.884 |

## By source

| Source | Test rows | Macro-F1 |
|---|---|---|
| s3_wiki_aggression | 11,528 | 0.8695 |
| s4_farah_zenodo | 1,139 | 0.7459 |
| s5_rizwan | 847 | 0.7932 |

## Hard negatives (casual profanity, should stay Neutral)

582 rows. False-alarm rate: **81.4%**. Predicted: {'Harassment': 427, 'Neutral': 108, 'Hate_speech': 47}

## C tuning on validation

| C | Val macro-F1 | Seconds |
|---|---|---|
| 0.1 | 0.7565 | 256.2 |
| 0.3 | 0.7568 | 201.7 |
| 1.0 | 0.7314 | 141.7 |
| 3.0 | 0.7338 | 147.4 |

## Top features per class (what the model relies on)

- **Harassment**: `char__uck`, `word__ass`, `char__fuc`, `char__fuck`, `word__fuck`, `word__bc`, `word__shit`, `word__idiot`, `char__ fuc`, `char__shit`, `word__you`, `char__ fuck`, `word__bitch`, `word__cunt`, `word__moron`
- **Hate_speech**: `word__halala`, `word__khusray`, `word__randi`, `word__hijra`, `word__yahodi`, `word__yahoodi`, `char__ rand`, `char__di `, `word__athiest`, `word__kaafir`, `char__ hij`, `char__ ran`, `word__ghasti`, `word__kanjeri`, `word__harami`
- **Neutral**: `char__ :`, `word__thank you`, `word__thank`, `word__دل`, `char__re`, `word__but`, `char__) `, `char__on`, `char__ w`, `word__ووٹ`, `char__ou`, `word__thi`, `word__محبت`, `word__luck`, `word__for your`
- **Threat**: `word__نگا`, `word__آباد پہنچنا`, `word__تمہ`, `word__آنکھ نکلنا`, `word__تمہ قتل`, `word__نہ ھو`, `word__گی`, `word__بہت بد`, `word__رکھنا دینا`, `word__عزت ہونا`, `word__باعزت`, `word__اگر عمران`, `word__نہ نکلنا`, `word__قریب`, `word__پنگا`

## Notes for the report

- Threat has very few test rows, so its recall moves a lot with each prediction.
- Hate speech exists only in Roman Urdu and Threat only in Urdu script: check the by-language table and the top features for a language shortcut instead of real meaning.
