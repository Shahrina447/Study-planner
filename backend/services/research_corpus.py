import csv
from pathlib import Path


class ResearchCorpus:
    def __init__(self, path: Path):
        self.path = path
        self.rows: list[dict] = []
        self.sources: dict[str, str] = {}

    def load(self) -> None:
        if not self.path.exists():
            self.rows = []
            return

        self.sources = self._load_sources()
        with self.path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            self.rows = [
                self._normalize_row(index, row)
                for index, row in enumerate(reader, 1)
                if self._row_has_content(row)
            ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[dict]:
        if not self.rows:
            return []

        query_terms = self._terms(query)
        scored = []
        for row in self.rows:
            if category and row["category"] != category:
                continue

            haystack = " ".join(
                [
                    row["category"],
                    row["question"],
                    row["answer"],
                    row["summary"],
                ]
            )
            terms = self._terms(haystack)
            score = self._score(query_terms, terms)
            scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = scored[:top_k]

        if query_terms and selected and selected[0][0] > 0:
            return [self._to_chunk(row, score) for score, row in selected]

        return [self._to_chunk(row, 0.0) for _, row in selected]

    def _normalize_row(self, index: int, row: dict) -> dict:
        if "chunk_id" in row:
            return self._normalize_mindbridge_row(index, row)

        row_number = (row.get("#") or str(index)).strip() or str(index)
        category = (row.get("Category") or "Research Corpus").strip()
        question = (row.get("Question") or "").strip()
        answer = (row.get("Detailed Answer") or "").strip()
        summary = (row.get("Key Points (Summary)") or "").strip()
        source = (row.get("Source / URL") or "qa_corpus.csv").strip()

        return {
            "id": f"QA_{int(row_number):03d}" if row_number.isdigit() else f"QA_{index:03d}",
            "source_file": "qa_corpus.csv",
            "category": category,
            "question": question,
            "answer": answer,
            "summary": summary,
            "source_url": source,
            "content": self._format_content(category, question, answer, summary, source),
            "topic": category,
            "risk_level": "L0_NORMAL",
            "title": question.rstrip("?"),
            "source_id": "",
            "allowed_use": "Academic and study support",
            "blocked_use": "Diagnosis; medication; clinical treatment",
            "language": "English",
        }

    def _normalize_mindbridge_row(self, index: int, row: dict) -> dict:
        chunk_id = (row.get("chunk_id") or f"CHUNK_{index:03d}").strip()
        title = (row.get("title") or "").strip()
        text = (row.get("text") or "").strip()
        category = (row.get("category") or "study_support").strip()
        source_id = (row.get("source_id") or "").strip()
        return {
            "id": chunk_id,
            "source_file": "mindbridge_final_corpus.csv",
            "category": category,
            "question": title,
            "answer": text,
            "summary": "",
            "source_url": self.sources.get(source_id, source_id),
            "content": text,
            "topic": (row.get("topic") or "Study planning").strip(),
            "risk_level": (row.get("risk_level") or "L0_NORMAL").strip(),
            "title": title,
            "source_id": source_id,
            "allowed_use": (row.get("allowed_use") or "").strip(),
            "blocked_use": (row.get("blocked_use") or "").strip(),
            "language": (row.get("language") or "English").strip(),
        }

    def _format_content(
        self,
        category: str,
        question: str,
        answer: str,
        summary: str,
        source: str,
    ) -> str:
        parts = [
            f"Category: {category}",
            f"Research question: {question}",
            f"Detailed answer: {answer}",
        ]
        if summary:
            parts.append(f"Key points: {summary}")
        if source:
            parts.append(f"Source: {source}")
        return "\n".join(parts)

    def _to_chunk(self, row: dict, score: float) -> dict:
        return {
            "id": row["id"],
            "chunk_id": row["id"],
            "source_file": row["source_file"],
            "content": row["content"],
            "similarity": min(score, 1.0),
            "category": row["category"],
            "source_url": row["source_url"],
        }

    def _terms(self, text: str) -> set[str]:
        return {
            word
            for word in "".join(
                character.lower() if character.isalnum() else " "
                for character in text
            ).split()
            if len(word) > 2
        }

    def _score(self, query_terms: set[str], document_terms: set[str]) -> float:
        if not query_terms or not document_terms:
            return 0.0
        overlap = len(query_terms & document_terms)
        return overlap / len(query_terms)

    def _row_has_content(self, row: dict) -> bool:
        return bool(
            (row.get("Question") or row.get("title") or "").strip()
            or (row.get("Detailed Answer") or row.get("text") or "").strip()
        )

    def _load_sources(self) -> dict[str, str]:
        sources_path = self.path.with_name("mindbridge_final_sources.csv")
        if not sources_path.exists():
            return {}
        with sources_path.open(newline="", encoding="utf-8-sig") as csv_file:
            return {
                (row.get("source_id") or "").strip(): (
                    row.get("source_link_or_reference") or ""
                ).strip()
                for row in csv.DictReader(csv_file)
            }


research_corpus = ResearchCorpus(
    Path(__file__).resolve().parent.parent
    / "data"
    / "mindbridge_final_corpus.csv"
)
