import json

from api.schemas import QuizGenerateRequest
from config import settings
from rag.db import db
from services.orchestrator import orchestrator


class QuizService:
    async def generate_quiz(self, request: QuizGenerateRequest):
        sample_chunks = await self._get_sample_chunks(request.source_file)

        if not sample_chunks:
            return {
                "status": "error",
                "message": "No documents uploaded yet. Please upload a document first.",
            }

        meaningful_chunks = [
            chunk
            for chunk in sample_chunks
            if self._is_meaningful(chunk["content"])
        ]
        if not meaningful_chunks:
            meaningful_chunks = sample_chunks

        context = "\n\n---\n\n".join(
            chunk["content"] for chunk in meaningful_chunks
        )
        prompt = self._build_quiz_prompt(request.num_questions, context)

        if not orchestrator.client:
            return {
                "status": "error",
                "message": "MISTRAL_API_KEY is missing in backend/.env",
            }

        try:
            response = await orchestrator.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            quiz_data = self._parse_quiz_json(
                response.choices[0].message.content.strip()
            )
            cleaned = self._clean_quiz_items(quiz_data)

            if not cleaned:
                return {
                    "status": "error",
                    "message": "Model returned an empty quiz. Please try again.",
                }

            return {"status": "success", "quiz": cleaned}
        except json.JSONDecodeError as error:
            return {
                "status": "error",
                "message": f"Could not parse quiz JSON: {error}. Please try again.",
            }
        except Exception as error:
            return {
                "status": "error",
                "message": f"Error generating quiz: {error}",
            }

    async def _get_sample_chunks(self, source_file: str | None) -> list[dict]:
        if not db.pool or not db.vector_enabled:
            raise RuntimeError("PostgreSQL with pgvector is not available.")

        async with db.pool.acquire() as conn:
            if source_file:
                rows = await conn.fetch(
                    """
                    SELECT content
                    FROM corpus_chunks
                    WHERE source_file = $1
                      AND embedding IS NOT NULL
                    ORDER BY random()
                    LIMIT 20
                    """,
                    source_file,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT content
                    FROM corpus_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY random()
                    LIMIT 20
                    """
                )
            return [{"content": row["content"]} for row in rows]

    def _is_meaningful(self, text: str) -> bool:
        stripped = text.strip()
        if len(stripped) < 80:
            return False

        alpha_ratio = sum(
            character.isalpha() or character.isspace()
            for character in stripped
        ) / max(len(stripped), 1)
        return alpha_ratio >= 0.5

    def _build_quiz_prompt(self, num_questions: int, context: str) -> str:
        return (
            "You are a university-level study assistant helping a student prepare for an exam.\n"
            "Below are passages extracted from a student's uploaded document.\n\n"
            f"Your task: Generate exactly {num_questions} meaningful study questions based SOLELY on the "
            "CONCEPTS, FACTS, DEFINITIONS, PROCESSES, or ARGUMENTS present in the passages below.\n\n"
            "STRICT RULES:\n"
            "- Questions MUST test understanding of the subject matter (concepts, definitions, processes, arguments, comparisons)\n"
            "- Do NOT ask about the document itself, its filename, file format, word count, structure, or metadata\n"
            "- Do NOT ask 'what is discussed in this document' or similar meta-questions\n"
            "- Every answer MUST be directly supported by information in the passages\n"
            "- Use a mix of difficulty levels: Easy (recall), Medium (comprehension), Hard (analysis/application)\n\n"
            "Return ONLY a valid JSON array. No explanation, no markdown, no extra text outside the array.\n"
            'Each element: {"q": "<question>", "a": "<detailed answer from the text>", "diff": "Easy|Medium|Hard"}\n\n'
            f"Passages:\n{context}"
        )

    def _parse_quiz_json(self, text: str):
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end < start:
            raise json.JSONDecodeError(
                "Model did not return a valid JSON array",
                text,
                0,
            )

        return json.loads(text[start : end + 1])

    def _clean_quiz_items(self, quiz_data) -> list[dict]:
        cleaned = []
        for item in quiz_data:
            if isinstance(item, dict) and "q" in item and "a" in item:
                cleaned.append(
                    {
                        "q": str(item.get("q", "")),
                        "a": str(item.get("a", "")),
                        "diff": str(item.get("diff", "Medium")),
                    }
                )
        return cleaned


quiz_service = QuizService()
