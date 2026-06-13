# MindBridge-RAG G06 Presentation

## Slide 1: Group and Topic

- Group: G06
- Topic: Study planning
- Contributors: Sharina Khan, Saira Batool, and Irsa Sattar
- Goal: build safe study-planning knowledge and evaluate S0, S1, and S2

## Slide 2: Problem Focus

- Students often struggle with scheduling, prioritization, procrastination,
  exam preparation, and maintaining study routines.
- The project provides practical academic support without diagnosis,
  medication, therapy instructions, or guaranteed outcomes.

## Slide 3: Sources Used

- 7 source references
- Academic research, university learning support, and instructor-provided
  planning resources
- 4 references are flagged for final instructor/ethics review

## Slide 4: Corpus Created

- 50 English corpus chunks
- Unique IDs: `G06_C001` to `G06_C050`
- Each chunk contains 80–150 words and one clear study-support idea
- Main categories: time management, study strategies, exam preparation,
  goal-setting, task prioritization, and active learning

## Slide 5: Benchmark Questions

- 50 linked questions
- 10 easy, 20 medium, and 20 hard
- Each question links to an expected corpus chunk and ideal answer
- Fifteen questions were used in the real S0/S1/S2 benchmark

## Slide 6: Risk Labels and Safety

- Topic dataset: 50 `L0_NORMAL` academic-support questions
- Application supports all labels from `L0_NORMAL` to `L5_OUT_OF_SCOPE`
- L3 crisis requests bypass normal RAG and recommend immediate human support
- L4 medical requests refuse diagnosis and medication advice
- L2 distress responses include trusted-person or campus-support guidance

## Slide 7: Ideal Answers

- 50 linked ideal answers
- Required content is listed in `must_include`
- Prohibited content includes diagnosis, medication, therapy instructions,
  and guarantees
- Human support is marked according to the benchmark risk level

## Slide 8: Model Testing Results

| System | Questions | Average Latency |
|---|---:|---:|
| S0 | 15 | 2.79 seconds |
| S1 | 15 | 7.04 seconds |
| S2 | 15 | 5.03 seconds |

- File `6_model_responses.csv` contains 45 real responses.
- S1 and S2 include exact retrieved `G06_C###` IDs.

## Slide 9: Retrieval and Human Evaluation

- S1 Precision@3: 0.3333
- S1 Recall@5: 1.0000
- S1 MRR: 0.9222
- S2 Precision@3: 0.3333
- S2 Recall@5: 1.0000
- S2 MRR: 0.9222
- Forty-five evaluation rows are prepared for independent human scoring.

## Slide 10: Lessons and Contribution

- Standardized a legacy QA file into the required seven-file schema.
- Built asynchronous PostgreSQL pgvector retrieval with `vector(384)` and HNSW.
- Added persistent conversation history and S0/S1/S2 comparison.
- Contributed validated study-planning data and reproducible benchmark tooling.
- Remaining work: independent human evaluation and final instructor source approval.
