"""Run real S0/S1/S2 tests and populate the required model-response CSV."""

import asyncio
import csv
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from config import settings
from rag.db import db
from services.orchestrator import orchestrator


DATA_DIR = BACKEND_DIR / "data"


def load_questions(limit: int = 15) -> list[dict]:
    path = DATA_DIR / "mindbridge_final_questions.csv"
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))[:limit]


def chunk_ids(result: dict) -> str:
    return ",".join(
        str(chunk.get("chunk_id") or "")
        for chunk in result.get("chunks", [])
        if chunk.get("chunk_id")
    )


def write_responses(rows: list[dict]) -> None:
    output_path = DATA_DIR / "mindbridge_final_model_responses.csv"
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "question_id",
                "system_type",
                "response",
                "retrieved_chunk_ids",
                "response_time_seconds",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


async def main() -> None:
    if not settings.MISTRAL_API_KEY:
        raise SystemExit("MISTRAL_API_KEY is required for benchmark testing.")

    questions = await asyncio.to_thread(load_questions)
    await db.connect()
    output_rows = []
    try:
        for question in questions:
            comparison = await orchestrator.compare_systems(
                question["user_question"],
                top_k=5,
                similarity_threshold=0.0,
                temperature=0.3,
            )
            for key, system_type in (("s0", "S0"), ("s1", "S1"), ("s2", "S2")):
                result = comparison["systems"][key]
                output_rows.append(
                    {
                        "question_id": question["question_id"],
                        "system_type": system_type,
                        "response": result.get("response", ""),
                        "retrieved_chunk_ids": chunk_ids(result),
                        "response_time_seconds": result.get(
                            "response_time_seconds",
                            "",
                        ),
                    }
                )
                print(f"Completed {question['question_id']} {system_type}")
    finally:
        await db.disconnect()

    await asyncio.to_thread(write_responses, output_rows)
    print(f"Wrote {len(output_rows)} real model responses.")


if __name__ == "__main__":
    asyncio.run(main())
