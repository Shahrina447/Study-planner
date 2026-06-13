# Group Report: MindBridge-RAG

## Group Information

**Group ID:** G06
**Assigned Topic:** Study planning
**Submission Date:** June 9, 2026

## Members

1. Name: Shahrina Khan | Roll No: 23018020084 | Role: Dataset and frontend contributor
2. Name: Abdullah Iqbal | Roll No: Not provided | Role: Integration and backend contributor
3. Name: Not provided | Roll No: Not provided | Role: Not provided
4. Name: Not provided | Roll No: Not provided | Role: Not provided
5. Name: Not provided | Roll No: Not provided | Role: Not provided

## 1. Topic Summary

The group developed study-planning and academic-skills content for
MindBridge-RAG. The topic covers weekly planning, time management,
goal-setting, exam preparation, task prioritization, active learning,
distraction management, study routines, and use of academic resources.
This content helps students turn large academic workloads into realistic,
structured actions without providing diagnosis, medication, or clinical advice.

## 2. Sources Used

Seven source references were used. They include academic research, academic
support material, university learning guidance, and instructor-provided study
resources. Four sources remain flagged for final instructor/ethics approval.

| Source ID | Source Title | Source Type | Why Used |
|---|---|---|---|
| G06_S001 | nced.info | Academic journal resource | Weekly planning and developmental mathematics evidence |
| G06_S002 | doi.org | Peer-reviewed research article | Learning strategies and academic achievement |
| G06_S003 | theshovelstudymethod.com | Instructor-provided study resource | Practical planning and study-habit examples |
| G06_S004 | creativecommons.org | Instructor-provided study resource | Study-plan and scheduling guidance |
| G06_S005 | bit.ly reference | Instructor-provided study resource | Planner templates and time-management tools |
| G06_S006 | UNC Learning Center | University academic support page | Evidence-based exam preparation techniques |
| G06_S007 | academicsupport.university.edu | University-style academic support page | Study routines and weekly planning |

## 3. Corpus Summary

**Total corpus chunks created:** 50

All chunks use unique `G06_C###` IDs, contain 80–150 words, are written in
English, and use the required MindBridge schema. The chunks cover one clear
study-support idea each and explicitly block diagnosis, medication, therapy
instructions, and guaranteed outcomes.

## 4. Benchmark Questions Summary

**Total benchmark questions created:** 50

| Difficulty | Count |
|---|---:|
| Easy | 10 |
| Medium | 20 |
| Difficult / Safety-sensitive | 20 |

Each question has a unique `G06_Q###` ID and links to its expected corpus chunk.

## 5. Risk Label Summary

| Risk Label | Count |
|---|---:|
| L0_NORMAL | 50 |
| L1_STRESS | 0 |
| L2_DISTRESS | 0 |
| L3_CRISIS | 0 |
| L4_MEDICAL | 0 |
| L5_OUT_OF_SCOPE | 0 |

The assigned topic dataset contains normal academic-support questions. The
application itself separately implements and verifies all L0–L5 routing,
including crisis and medical bypass behavior.

## 6. Model Testing Summary

Fifteen benchmark questions were tested on each required system. File
`6_model_responses.csv` contains 45 real responses, retrieved chunk IDs, and
measured response times.

| System | Count Tested | Average Response Time |
|---|---:|---:|
| S0: Basic chatbot without RAG | 15 | 2.79 seconds |
| S1: Basic RAG | 15 | 7.04 seconds |
| S2: Safety-aware RAG | 15 | 5.03 seconds |

## 7. Human Evaluation Summary

Forty-five rows are prepared in `7_human_evaluation.csv`, one for every tested
question/system pair. Independent human evaluators must complete the scores.
No human ratings have been fabricated.

| Metric | Average Score |
|---|---:|
| Relevance | Pending human evaluation |
| Helpfulness | Pending human evaluation |
| Faithfulness | Pending human evaluation |
| Safety | Pending human evaluation |
| Clarity | Pending human evaluation |

## 8. Key Observations

1. PostgreSQL pgvector retrieval returned standardized `G06_C###` chunk IDs.
2. S1 and S2 both achieved Recall@5 of 1.00 and MRR of 0.9222 on the 15 tested questions.
3. All 50 corpus records have 384-dimensional embeddings and an HNSW cosine index.
4. S0 was fastest because it performs no retrieval; S1 and S2 include retrieval and grounding.
5. S2 applies L0–L5 risk routing and bypasses normal generation for crisis,
   medical, and out-of-scope requests.

## 9. Problems Faced

- The original QA CSV did not match the required MindBridge schemas and had to
  be normalized into seven linked files.
- Some source references require final instructor/ethics approval.
- Embedding-model loading and external model calls increased first-run latency.
- Human evaluation cannot be completed automatically without violating the
  requirement for independent human judgment.

## 10. Contribution to Final Paper

The group contributes a validated study-planning corpus, benchmark questions,
ideal answers, risk labels, real S0/S1/S2 response records, exact retrieval IDs,
and response latency measurements. The application supplies an asynchronous
pgvector RAG implementation and safety-routing framework that can support the
paper’s comparison of relevance, faithfulness, safety, and latency.

## 11. Declaration

We confirm that:

- We did not include private real student stories.
- We did not include medical diagnosis or medication advice.
- We used safe, general, student-support content.
- We followed the assigned CSV templates and risk-label format.
- Human evaluation scores remain pending independent review and were not invented.
