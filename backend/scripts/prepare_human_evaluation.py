"""Prepare the human evaluation worksheet from real benchmark responses."""

import csv
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


def main() -> None:
    responses_path = DATA_DIR / "mindbridge_final_model_responses.csv"
    evaluation_path = DATA_DIR / "mindbridge_final_human_evaluation.csv"

    with responses_path.open(encoding="utf-8-sig", newline="") as csv_file:
        responses = list(csv.DictReader(csv_file))

    rows = [
        {
            "question_id": row["question_id"],
            "system_type": row["system_type"],
            "relevance_score": "",
            "helpfulness_score": "",
            "faithfulness_score": "",
            "safety_score": "",
            "clarity_score": "",
            "unsafe_flag": "",
            "comments": "Pending independent human evaluation.",
        }
        for row in responses
    ]

    with evaluation_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "question_id",
                "system_type",
                "relevance_score",
                "helpfulness_score",
                "faithfulness_score",
                "safety_score",
                "clarity_score",
                "unsafe_flag",
                "comments",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Prepared {len(rows)} human-evaluation rows.")


if __name__ == "__main__":
    main()
