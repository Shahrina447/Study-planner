import re
import asyncio
from mistralai import Mistral
from config import settings
from rag.retriever import retriever


class StudyOrchestrator:
    def __init__(self):
        if settings.MISTRAL_API_KEY:
            self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        else:
            self.client = None

    # ── Text helpers ──────────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """Normalise raw PDF-extracted text into clean paragraph prose."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = re.split(r"\n{2,}", text)
        cleaned = []
        for para in paragraphs:
            lines = [l.strip() for l in para.split("\n") if l.strip()]
            lines = [
                l for l in lines
                if not re.fullmatch(r"[\d\s\-–—|/\\]+", l)
                and len(l) > 3
            ]
            if not lines:
                continue
            joined = ""
            for line in lines:
                if joined and joined[-1] not in ".!?:;,\"')}]":
                    joined += " " + line
                else:
                    joined = (joined + " " + line).strip() if joined else line
            if joined:
                cleaned.append(joined)
        return "\n\n".join(cleaned)

    def _format_chunks_for_display(self, context_chunks: list[dict]) -> list[dict]:
        """Return cleaned chunk dicts for the frontend compare/corpus view."""
        result = []
        for i, chunk in enumerate(context_chunks, 1):
            similarity = chunk.get("similarity")
            result.append({
                "index": i,
                "source": chunk["source_file"],
                "content": self._clean_text(chunk["content"]),
                "similarity": round(float(similarity), 4) if similarity is not None else None,
            })
        return result

    # ── Prompts ───────────────────────────────────────────────────────────────

    def _build_ai_prompt(self, user_message: str, context_text: str) -> str:
        """
        AI mode: Mistral uses RAG context as grounding but may draw on its own
        knowledge to fill gaps and produce a well-rounded answer.
        """
        return f"""You are a knowledgeable study planner and teaching assistant.
The student's uploaded study documents are provided below as your primary knowledge source.

Your job:
1. **Answer questions** – synthesise an accurate, helpful answer from the provided passages.
   - Piece together information from multiple chunks even if no single chunk fully answers the question.
   - Use Markdown (bold key terms, bullet lists, short paragraphs).
   - You may supplement with general knowledge where the documents leave gaps, but always ground your answer in the provided material first.
2. **Create study plans** – if asked, produce a personalised weekly plan:
   - Extract topics/subtopics from the document chunks.
   - Estimate study time per topic based on content depth.
   - Distribute across available days; mark high-priority topics.
   - Format: `Day N: Topic — <name> | Duration — <X h> | Priority — High/Medium/Low`
3. Never flatly refuse a reasonable study-related question. If the documents don't cover a topic, say so briefly and then answer from general knowledge.

--- Retrieved study material ---
{context_text}
--- End of study material ---

Student question: {user_message}
"""

    def _build_corpus_prompt(self, user_message: str, grouped_context: str) -> str:
        """
        Corpus mode: Mistral is only allowed to use the retrieved passages.
        It must cite sources and must NOT add outside knowledge.
        """
        return f"""You are a document-grounded study assistant.
A student asked: "{user_message}"

Below are the exact passages retrieved from their uploaded study documents (grouped by source file).
Your answer MUST be based solely on these passages — do not add any information from outside them.

{grouped_context}

Write a well-structured answer in Markdown:
- Open with a short **bold summary** (1-2 sentences)
- Use `##` headings for logical sections
- Use bullet points or numbered lists for steps/features
- **Bold** key terms
- Cite the source file inline, e.g. (make-a-7-day-study-plan.pdf)
- End with a `## Summary` section (2-3 bullet points)
- Do NOT invent information not present in the passages above
"""

    # ── Shared retrieval helper ───────────────────────────────────────────────

    async def _retrieve(
        self,
        query: str,
        top_k: int,
        similarity_threshold: float,
        source_file: str | None,
    ) -> tuple[list[dict], str, str, dict[str, list[str]]]:
        """
        Returns (chunks, flat_context_text, grouped_context_text, source_groups).
        flat_context_text  – used for AI mode prompt
        grouped_context    – used for corpus mode prompt
        """
        chunks = await retriever.search(
            query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            source_file=source_file,
        )

        # Flat context for AI prompt
        flat_context = "\n\n".join(
            f"Source: {c['source_file']}\nContent: {c['content']}"
            for c in chunks
        )

        # Grouped + cleaned context for corpus prompt
        source_groups: dict[str, list[str]] = {}
        for chunk in chunks:
            cleaned = self._clean_text(chunk["content"])
            if cleaned:
                source_groups.setdefault(chunk["source_file"], []).append(cleaned)

        grouped_context = "\n\n".join(
            f"[{src}]\n" + " ".join(passages)
            for src, passages in source_groups.items()
        )

        return chunks, flat_context, grouped_context, source_groups

    # ── Public methods ────────────────────────────────────────────────────────

    async def chat(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        temperature: float = 0.3,
        source_file: str | None = None,
    ):
        """
        AI mode — Mistral synthesises an answer grounded in RAG context.
        """
        chunks, flat_context, _, _ = await self._retrieve(
            user_message, top_k, similarity_threshold, source_file
        )
        sources = list(set(c["source_file"] for c in chunks))

        if not self.client:
            return {
                "status": "error",
                "response": "MISTRAL_API_KEY is missing in backend/.env",
                "sources": sources,
            }

        try:
            resp = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[
                    {"role": "user", "content": self._build_ai_prompt(user_message, flat_context)}
                ],
                temperature=temperature,
            )
            return {
                "status": "success",
                "response": resp.choices[0].message.content,
                "sources": sources,
            }
        except Exception as e:
            return {"status": "error", "response": f"Mistral error: {e}", "sources": sources}

    async def corpus_only(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        temperature: float = 0.3,
        source_file: str | None = None,
    ):
        """
        Corpus mode — answer is built ONLY from retrieved RAG passages.
        No outside knowledge from Mistral; the model is just a formatter/synthesiser
        of the raw document text.
        """
        chunks, _, grouped_context, _ = await self._retrieve(
            user_message, top_k, similarity_threshold, source_file
        )
        sources = list(set(c["source_file"] for c in chunks))
        display_chunks = self._format_chunks_for_display(chunks)

        if not chunks:
            return {
                "status": "success",
                "response": "No relevant passages found in your uploaded documents for this query.",
                "sources": [],
                "chunks": [],
            }

        # If no Mistral client, fall back to returning the raw cleaned passages
        if not self.client:
            return {
                "status": "success",
                "response": grouped_context,
                "sources": sources,
                "chunks": display_chunks,
            }

        try:
            resp = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[
                    {"role": "user", "content": self._build_corpus_prompt(user_message, grouped_context)}
                ],
                temperature=temperature,
            )
            return {
                "status": "success",
                "response": resp.choices[0].message.content.strip(),
                "sources": sources,
                "chunks": display_chunks,
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Mistral error: {e}",
                "sources": sources,
                "chunks": display_chunks,
            }

    async def compare(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        temperature: float = 0.3,
        source_file: str | None = None,
    ):
        """
        Compare mode — runs AI and Corpus calls in parallel and returns both.
        AI tab  : Mistral with its own knowledge + RAG grounding
        Corpus tab: Mistral restricted to RAG passages only
        """
        chunks, flat_context, grouped_context, _ = await self._retrieve(
            user_message, top_k, similarity_threshold, source_file
        )
        sources = list(set(c["source_file"] for c in chunks))
        display_chunks = self._format_chunks_for_display(chunks)

        if not self.client:
            return {
                "status": "error",
                "ai_response": "MISTRAL_API_KEY is missing in backend/.env",
                "corpus_response": grouped_context,
                "sources": sources,
                "chunks": display_chunks,
            }

        try:
            ai_task = self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[
                    {"role": "user", "content": self._build_ai_prompt(user_message, flat_context)}
                ],
                temperature=temperature,
            )
            corpus_task = self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[
                    {"role": "user", "content": self._build_corpus_prompt(user_message, grouped_context)}
                ],
                temperature=temperature,
            )
            ai_resp, corpus_resp = await asyncio.gather(ai_task, corpus_task)
            return {
                "status": "success",
                "ai_response": ai_resp.choices[0].message.content,
                "corpus_response": corpus_resp.choices[0].message.content.strip(),
                "sources": sources,
                "chunks": display_chunks,
            }
        except Exception as e:
            return {
                "status": "error",
                "ai_response": f"Mistral error: {e}",
                "corpus_response": grouped_context,
                "sources": sources,
                "chunks": display_chunks,
            }


orchestrator = StudyOrchestrator()
