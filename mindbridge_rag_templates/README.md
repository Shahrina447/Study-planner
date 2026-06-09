# MindBridge-RAG Template Pack

This folder contains the required submission templates for each group.

## Required files

1. `1_sources.csv`
2. `2_corpus_chunks.csv`
3. `3_benchmark_questions.csv`
4. `4_ideal_answers.csv`
5. `5_risk_labels.csv`
6. `6_model_responses.csv`
7. `7_human_evaluation.csv`
8. `group_report.md`

## Risk labels

Use only these labels:

- `L0_NORMAL`: Normal study or academic support
- `L1_STRESS`: Mild stress, worry, nervousness
- `L2_DISTRESS`: Strong emotional distress or hopelessness
- `L3_CRISIS`: Self-harm, suicide, violence, immediate danger
- `L4_MEDICAL`: Diagnosis, medication, clinical treatment request
- `L5_OUT_OF_SCOPE`: Not related to student support

## System types

Use only these values in `6_model_responses.csv` and `7_human_evaluation.csv`:

- `S0`: Basic chatbot without RAG
- `S1`: Basic RAG
- `S2`: Safety-aware RAG

## Minimum per group

- 3 safe sources
- 30 corpus chunks
- 30 benchmark questions
- 30 ideal answers
- 30 risk labels
- 15 evaluated model responses
- 1 group report

## Safety rules

- Do not include private real student stories.
- Do not include medical diagnosis or medication advice.
- Do not write therapy or treatment instructions.
- Use safe, general, student-support language.
- Crisis examples must be synthetic and handled with safe escalation language.
