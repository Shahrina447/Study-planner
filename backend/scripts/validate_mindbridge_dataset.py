"""Validate integrated MindBridge CSV files against the project guidelines."""

import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VALID_RISKS = {
    "L0_NORMAL",
    "L1_STRESS",
    "L2_DISTRESS",
    "L3_CRISIS",
    "L4_MEDICAL",
    "L5_OUT_OF_SCOPE",
}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
REVIEW_SOURCE_HOSTS = {
    "theshovelstudymethod.com",
    "bit.ly",
    "creativecommons.org",
    "academicsupport.university.edu",
}


def load(name: str) -> list[dict]:
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    errors: list[str] = []
    sources = load("mindbridge_final_sources.csv")
    corpus = load("mindbridge_final_corpus.csv")
    questions = load("mindbridge_final_questions.csv")
    answers = load("mindbridge_final_ideal_answers.csv")
    labels = load("mindbridge_final_risk_labels.csv")
    responses = load("mindbridge_final_model_responses.csv")
    evaluations = load("mindbridge_final_human_evaluation.csv")

    source_ids = {row["source_id"] for row in sources}
    chunk_ids = [row["chunk_id"] for row in corpus]
    question_ids = [row["question_id"] for row in questions]
    answer_ids = {row["question_id"] for row in answers}
    label_ids = {row["question_id"] for row in labels}

    require(len(sources) >= 3, "At least 3 sources are required.", errors)
    require(len(corpus) >= 30, "At least 30 corpus chunks are required.", errors)
    require(len(questions) >= 30, "At least 30 questions are required.", errors)
    require(len(answers) >= 30, "At least 30 ideal answers are required.", errors)
    require(len(labels) >= 30, "At least 30 risk labels are required.", errors)
    require(len(chunk_ids) == len(set(chunk_ids)), "Chunk IDs must be unique.", errors)
    require(
        len(question_ids) == len(set(question_ids)),
        "Question IDs must be unique.",
        errors,
    )
    require(
        all(row["source_id"] in source_ids for row in corpus),
        "Every corpus source_id must exist in sources.",
        errors,
    )
    require(
        all(row["risk_level"] in VALID_RISKS for row in corpus),
        "Corpus contains an invalid risk label.",
        errors,
    )
    require(
        all(row["expected_risk_level"] in VALID_RISKS for row in questions),
        "Questions contain an invalid risk label.",
        errors,
    )
    require(
        all(row["difficulty"] in VALID_DIFFICULTIES for row in questions),
        "Questions contain an invalid difficulty.",
        errors,
    )
    require(set(question_ids) == answer_ids, "Every question needs one ideal answer.", errors)
    require(set(question_ids) == label_ids, "Every question needs one risk label.", errors)
    require(
        all(
            row["expected_risk_level"]
            == next(
                label["risk_label"]
                for label in labels
                if label["question_id"] == row["question_id"]
            )
            for row in questions
        ),
        "Question and risk-label files disagree.",
        errors,
    )
    require(
        all(row["system_type"] in {"S0", "S1", "S2"} for row in responses),
        "Model responses contain an invalid system type.",
        errors,
    )
    require(
        all(row["question_id"] in set(question_ids) for row in responses),
        "Model responses contain an unknown question ID.",
        errors,
    )
    require(
        all(row["system_type"] in {"S0", "S1", "S2"} for row in evaluations),
        "Human evaluations contain an invalid system type.",
        errors,
    )
    require(
        all(
            1 <= int(row[field]) <= 5
            for row in evaluations
            for field in (
                "relevance_score",
                "helpfulness_score",
                "faithfulness_score",
                "safety_score",
                "clarity_score",
            )
        ),
        "Human evaluation scores must be between 1 and 5.",
        errors,
    )
    require(
        all(row["unsafe_flag"] in {"0", "1"} for row in evaluations),
        "unsafe_flag must be 0 or 1.",
        errors,
    )
    require(
        all(
            80 <= len(row["text"].split()) <= 150
            for row in corpus
        ),
        "Every corpus chunk must contain 80-150 words.",
        errors,
    )

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))

    print(f"Sources: {len(sources)}")
    print(f"Corpus chunks: {len(corpus)}")
    print(f"Questions: {len(questions)}")
    print(f"Difficulty: {dict(Counter(row['difficulty'] for row in questions))}")
    print(f"Risk labels: {dict(Counter(row['risk_label'] for row in labels))}")
    print(f"Model responses: {len(responses)} (testing phase)")
    print(f"Human evaluations: {len(evaluations)} (human phase)")
    review_sources = [
        row["source_link_or_reference"]
        for row in sources
        if urlparse(row["source_link_or_reference"]).netloc.lower().removeprefix("www.")
        in REVIEW_SOURCE_HOSTS
    ]
    if review_sources:
        print(
            "WARNING: Instructor/ethics source review required for: "
            + ", ".join(review_sources)
        )
    print("Dataset validation passed.")


if __name__ == "__main__":
    main()
