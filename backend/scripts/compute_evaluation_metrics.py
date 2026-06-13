"""Compute final MindBridge metrics from real model and human evaluation CSVs."""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load(name: str) -> list[dict]:
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def ids(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.replace(";", ",").split(",")
        if item.strip()
    ]


def write_results(rows: list[dict]) -> None:
    path = DATA_DIR / "mindbridge_final_results.csv"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["metric", "system_type", "value", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    questions = {
        row["question_id"]: ids(row["expected_chunk_ids"])
        for row in load("mindbridge_final_questions.csv")
    }
    responses = load("mindbridge_final_model_responses.csv")
    evaluations = load("mindbridge_final_human_evaluation.csv")
    if not responses:
        raise SystemExit(
            "Real model responses are required before metrics can be computed."
        )

    results: list[dict] = []
    response_groups: dict[str, list[dict]] = defaultdict(list)
    evaluation_groups: dict[str, list[dict]] = defaultdict(list)
    for row in responses:
        response_groups[row["system_type"]].append(row)
    for row in evaluations:
        if not row["relevance_score"].strip():
            continue
        evaluation_groups[row["system_type"]].append(row)

    for system, rows in sorted(response_groups.items()):
        latencies = [
            float(row["response_time_seconds"])
            for row in rows
            if row["response_time_seconds"].strip()
        ]
        if latencies:
            results.append(
                {
                    "metric": "average_response_latency_seconds",
                    "system_type": system,
                    "value": f"{mean(latencies):.4f}",
                    "notes": f"{len(latencies)} measured responses",
                }
            )

        if system not in {"S1", "S2"}:
            continue
        precisions = []
        recalls = []
        reciprocal_ranks = []
        for row in rows:
            expected = set(questions.get(row["question_id"], []))
            retrieved = ids(row["retrieved_chunk_ids"])
            if not expected:
                continue
            top_three = retrieved[:3]
            top_five = retrieved[:5]
            precisions.append(
                len(expected.intersection(top_three)) / max(len(top_three), 1)
            )
            recalls.append(len(expected.intersection(top_five)) / len(expected))
            rank = next(
                (
                    index
                    for index, chunk_id in enumerate(retrieved, 1)
                    if chunk_id in expected
                ),
                None,
            )
            reciprocal_ranks.append(1 / rank if rank else 0)
        for metric, values in (
            ("precision_at_3", precisions),
            ("recall_at_5", recalls),
            ("mrr", reciprocal_ranks),
        ):
            if values:
                results.append(
                    {
                        "metric": metric,
                        "system_type": system,
                        "value": f"{mean(values):.4f}",
                        "notes": f"{len(values)} benchmark questions",
                    }
                )

    score_fields = [
        "relevance_score",
        "helpfulness_score",
        "faithfulness_score",
        "safety_score",
        "clarity_score",
    ]
    for system, rows in sorted(evaluation_groups.items()):
        for field in score_fields:
            values = [float(row[field]) for row in rows if row[field].strip()]
            if values:
                results.append(
                    {
                        "metric": f"average_{field}",
                        "system_type": system,
                        "value": f"{mean(values):.4f}",
                        "notes": f"{len(values)} human evaluations",
                    }
                )
        unsafe = [int(row["unsafe_flag"]) for row in rows]
        results.append(
            {
                "metric": "unsafe_response_rate",
                "system_type": system,
                "value": f"{mean(unsafe):.4f}",
                "notes": f"{len(unsafe)} human evaluations",
            }
        )

    write_results(results)
    print(f"Wrote {len(results)} metrics to mindbridge_final_results.csv.")


if __name__ == "__main__":
    main()
