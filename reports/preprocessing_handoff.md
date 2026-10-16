# Preprocessing handoff

All five variants use the same canonical documents, queries, IDs and qrels.

| Language | Variant | Documents | Queries | Empty documents | Empty queries |
|---|---|---:|---:|---:|---:|
| vi | original | 10576 | 9985 | 0 | 0 |
| vi | stopword | 10576 | 9985 | 0 | 0 |
| vi | normalize | 10576 | 9985 | 0 | 0 |
| vi | tokenize | 10576 | 9985 | 0 | 0 |
| vi | combined | 10576 | 9985 | 0 | 0 |
| en | original | 3633 | 323 | 0 | 0 |
| en | stopword | 3633 | 323 | 0 | 0 |
| en | normalize | 3633 | 323 | 0 | 0 |
| en | tokenize | 3633 | 323 | 0 | 0 |
| en | combined | 3633 | 323 | 0 | 0 |

## Files

- Data: ../data/processed/vi and ../data/processed/en
- Examples: preprocessing_examples.md
- Validation: validation_report.json (available after full validation completes)
- Configuration and library versions: build_manifest.json
- Stopword sources: ../resources/stopwords/sources.json

## Integration still required

Person 2: confirm tokenizer input handling, disable unintended lowercase/stopword defaults, preserve compound tokens and IDs.
Person 3: use the same evaluation query IDs for every variant, preserve the original relevance levels.
No retrieval models or evaluation scores have been run in this step.