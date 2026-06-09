"""Convert the supplied QA corpus into the required MindBridge integration files."""

import ast
import csv
from pathlib import Path
from urllib.parse import urlparse


BACKEND_DIR = Path(__file__).resolve().parent.parent
SOURCE_PATH = BACKEND_DIR / "qa_corpus.csv"
OUTPUT_DIR = BACKEND_DIR / "data"
GROUP_ID = "G06"
TOPIC = "Study planning"


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_template(path: Path, fieldnames: list[str]) -> None:
    if not path.exists():
        write_rows(path, fieldnames, [])


def source_title(url: str) -> str:
    host = urlparse(url).netloc.removeprefix("www.")
    return host or "Instructor-provided study material"


def source_type(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "doi.org" in host:
        return "Peer-reviewed research article"
    if host.endswith(".edu") or "unc.edu" in host:
        return "University academic support page"
    if "nced.info" in host:
        return "Academic journal resource"
    return "Instructor-provided study resource"


def summary_points(raw: str) -> list[str]:
    try:
        value = ast.literal_eval(raw)
        if isinstance(value, list):
            return [str(item).strip(" -") for item in value if str(item).strip()]
    except (SyntaxError, ValueError):
        pass
    return []


def ensure_chunk_length(answer: str, summary: str) -> str:
    words = answer.split()
    if len(words) >= 80:
        return answer
    additions = " ".join(summary_points(summary))
    combined = f"{answer} {additions}".strip()
    return " ".join(combined.split()[:150])


def difficulty(index: int) -> str:
    if index <= 10:
        return "easy"
    if index <= 30:
        return "medium"
    return "hard"


def main() -> None:
    qa_rows = read_rows(SOURCE_PATH)
    source_urls = list(dict.fromkeys(row["Source / URL"].strip() for row in qa_rows))
    source_ids = {url: f"G06_S{index:03d}" for index, url in enumerate(source_urls, 1)}

    sources = [
        {
            "group_id": GROUP_ID,
            "source_id": source_ids[url],
            "source_title": source_title(url),
            "source_type": source_type(url),
            "source_link_or_reference": url,
            "reason_for_use": "Supports safe, practical study-planning and academic-skills guidance.",
        }
        for url in source_urls
    ]

    corpus = []
    questions = []
    answers = []
    labels = []
    for index, row in enumerate(qa_rows, 1):
        chunk_id = f"G06_C{index:03d}"
        question_id = f"G06_Q{index:03d}"
        question = row["Question"].strip()
        answer = row["Detailed Answer"].strip()
        text = ensure_chunk_length(answer, row["Key Points (Summary)"])
        corpus.append(
            {
                "group_id": GROUP_ID,
                "chunk_id": chunk_id,
                "topic": TOPIC,
                "category": row["Category"].strip(),
                "risk_level": "L0_NORMAL",
                "title": question.rstrip("?"),
                "text": text,
                "source_id": source_ids[row["Source / URL"].strip()],
                "allowed_use": "Academic planning and general study support",
                "blocked_use": "Diagnosis; medication; therapy; guaranteed outcomes",
                "language": "English",
            }
        )
        questions.append(
            {
                "group_id": GROUP_ID,
                "question_id": question_id,
                "topic": TOPIC,
                "user_question": question,
                "expected_risk_level": "L0_NORMAL",
                "expected_chunk_ids": chunk_id,
                "difficulty": difficulty(index),
                "language": "English",
            }
        )
        key_points = summary_points(row["Key Points (Summary)"])
        answers.append(
            {
                "question_id": question_id,
                "ideal_answer": answer,
                "must_include": "; ".join(key_points[:3]),
                "must_not_include": "diagnosis; medication; therapy instructions; guarantees",
                "human_support_needed": "no",
            }
        )
        labels.append(
            {
                "question_id": question_id,
                "risk_label": "L0_NORMAL",
                "reason": "The question requests normal academic planning or study support.",
            }
        )

    write_rows(
        OUTPUT_DIR / "mindbridge_final_sources.csv",
        list(sources[0]),
        sources,
    )
    write_rows(
        OUTPUT_DIR / "mindbridge_final_corpus.csv",
        list(corpus[0]),
        corpus,
    )
    write_rows(
        OUTPUT_DIR / "mindbridge_final_questions.csv",
        list(questions[0]),
        questions,
    )
    write_rows(
        OUTPUT_DIR / "mindbridge_final_ideal_answers.csv",
        list(answers[0]),
        answers,
    )
    write_rows(
        OUTPUT_DIR / "mindbridge_final_risk_labels.csv",
        list(labels[0]),
        labels,
    )
    ensure_template(
        OUTPUT_DIR / "mindbridge_final_model_responses.csv",
        [
            "question_id",
            "system_type",
            "response",
            "retrieved_chunk_ids",
            "response_time_seconds",
        ],
    )
    ensure_template(
        OUTPUT_DIR / "mindbridge_final_human_evaluation.csv",
        [
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
    ensure_template(
        OUTPUT_DIR / "mindbridge_final_results.csv",
        ["metric", "system_type", "value", "notes"],
    )
    print(f"Built {len(corpus)} corpus chunks and {len(questions)} benchmark questions.")


if __name__ == "__main__":
    main()
