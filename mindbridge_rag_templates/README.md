# MindBridge-RAG Group G06 Submission

**Topic:** Study planning
**Submission date:** June 9, 2026

## Included Files

| File | Status |
|---|---|
| `1_sources.csv` | Complete: 7 sources |
| `2_corpus_chunks.csv` | Complete: 50 validated chunks |
| `3_benchmark_questions.csv` | Complete: 50 questions |
| `4_ideal_answers.csv` | Complete: 50 linked answers |
| `5_risk_labels.csv` | Complete: 50 linked labels |
| `6_model_responses.csv` | Complete: 45 real S0/S1/S2 responses |
| `7_human_evaluation.csv` | Prepared: 45 rows awaiting independent human scores |
| `group_report.md` | Complete with verified project results |
| `presentation_outline.md` | Complete 10-slide outline |

## Validation

- Unique chunk and question IDs
- Exact required CSV headers
- Corpus chunks contain 80–150 words
- Every question links to one ideal answer and risk label
- System types use only `S0`, `S1`, and `S2`
- Real response latency and retrieved chunk IDs are recorded

## Human Evaluation

The evaluation worksheet is fully mapped to tested responses. A human evaluator
must enter scores from 1–5 and set `unsafe_flag` to `0` or `1`. The score cells
are intentionally blank because automated or invented ratings must not be
presented as human evaluation.
