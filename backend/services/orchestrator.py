import re
import asyncio
from time import perf_counter
from mistralai import Mistral
from config import settings
from rag.retriever import retriever


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "should",
    "so",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "us",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "you",
    "your",
}


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

    def _tokenize(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9']+", text.lower())
            if len(token) > 2 and token not in STOPWORDS
        }

    def _scale_to_five(self, score: float) -> float:
        return round(1.0 + (max(0.0, min(score, 1.0)) * 4.0), 2)

    def _chunk_token_set(self, chunks: list[dict] | None) -> set[str]:
        if not chunks:
            return set()
        return self._tokenize(
            " ".join(self._clean_text(chunk.get("content", "")) for chunk in chunks)
        )

    def _average_chunk_similarity(self, chunks: list[dict] | None) -> float:
        if not chunks:
            return 0.0
        similarities = [
            float(chunk.get("similarity"))
            for chunk in chunks
            if chunk.get("similarity") is not None
        ]
        if not similarities:
            return 0.0
        return max(0.0, min(sum(similarities) / len(similarities), 1.0))

    def _build_response_metrics(
        self,
        user_message: str,
        response_text: str,
        chunks: list[dict] | None,
        risk: dict | None = None,
        status: str = "success",
    ) -> dict[str, float]:
        question_tokens = self._tokenize(user_message)
        response_tokens = self._tokenize(response_text)
        chunk_tokens = self._chunk_token_set(chunks)
        response_lower = response_text.lower()
        response_length = max(len(response_tokens), 1)
        response_size = len(response_tokens)

        question_overlap = len(question_tokens & response_tokens) / max(len(question_tokens), 1)
        response_focus = len(question_tokens & response_tokens) / response_length
        length_score = 1.0 - min(abs(response_size - 120) / 120, 1.0)

        relevance_raw = (0.65 * question_overlap) + (0.2 * response_focus) + (0.15 * length_score)
        relevance = self._scale_to_five(relevance_raw)

        if chunks:
            grounded_overlap = len(response_tokens & chunk_tokens) / response_length
            grounding_raw = (
                0.65 * grounded_overlap
                + 0.2 * self._average_chunk_similarity(chunks)
                + 0.15 * min(len(chunks) / 5, 1.0)
            )
        else:
            grounding_raw = 0.18 * length_score
            if status == "error":
                grounding_raw *= 0.5
        grounding = self._scale_to_five(grounding_raw)

        safety_raw = 0.72
        unsafe_terms = (
            "suicide",
            "self-harm",
            "self harm",
            "kill myself",
            "hurt myself",
            "medication",
            "diagnose",
            "diagnosis",
            "violent",
            "weapon",
            "malware",
        )
        if any(term in response_lower for term in unsafe_terms):
            safety_raw -= 0.45
        supportive_terms = (
            "trusted person",
            "campus",
            "counselor",
            "counsellor",
            "support service",
            "emergency",
            "study plan",
            "break the task down",
            "step by step",
            "practical",
        )
        if any(term in response_lower for term in supportive_terms):
            safety_raw += 0.18
        if risk and risk.get("label") in {"L3_CRISIS", "L4_MEDICAL", "L5_OUT_OF_SCOPE"}:
            if any(term in response_lower for term in supportive_terms):
                safety_raw += 0.12
            else:
                safety_raw -= 0.12
        if status == "error":
            safety_raw -= 0.2
        safety = self._scale_to_five(safety_raw)

        structure_bonus = 0.0
        if re.search(r"(^|\n)\s*(?:[-*]|\d+\.)\s+", response_text):
            structure_bonus += 0.35
        if re.search(r"^#{1,3}\s+", response_text, flags=re.MULTILINE):
            structure_bonus += 0.25
        if response_size >= 40:
            structure_bonus += 0.2
        if 70 <= response_size <= 220:
            structure_bonus += 0.2
        clarity_raw = (0.45 * length_score) + (0.35 * structure_bonus) + (0.2 * relevance_raw)
        clarity = self._scale_to_five(clarity_raw)

        return {
            "relevance_score": relevance,
            "groundedness_score": grounding,
            "safety_score": safety,
            "clarity_score": clarity,
        }

    def _format_chunks_for_display(self, context_chunks: list[dict]) -> list[dict]:
        """Return cleaned chunk dicts for the frontend compare/corpus view."""
        result = []
        for i, chunk in enumerate(context_chunks, 1):
            similarity = chunk.get("similarity")
            result.append({
                "index": i,
                "chunk_id": str(chunk.get("chunk_id") or chunk.get("id") or f"C{i:03d}"),
                "source": chunk["source_file"],
                "content": self._clean_text(chunk["content"]),
                "similarity": round(float(similarity), 4) if similarity is not None else None,
                "category": chunk.get("category"),
                "source_url": chunk.get("source_url"),
            })
        return result

    def _classify_risk(self, user_message: str) -> dict:
        text = user_message.lower()
        crisis_terms = [
            "kill myself",
            "suicide",
            "end my life",
            "harm myself",
            "hurt myself",
            "self-harm",
            "self harm",
            "want to die",
            "violent",
            "hurt someone",
        ]
        medical_terms = [
            "diagnose",
            "diagnosis",
            "do i have depression",
            "do i have anxiety",
            "medicine",
            "medication",
            "antidepressant",
            "clinical treatment",
            "panic disorder",
            "mental illness",
        ]
        distress_terms = [
            "hopeless",
            "can't handle",
            "cannot handle",
            "overwhelmed",
            "give up",
            "breaking down",
            "can't cope",
            "cannot cope",
        ]
        stress_terms = [
            "stress",
            "stressed",
            "nervous",
            "worried",
            "anxious",
            "pressure",
            "burnout",
            "afraid",
        ]
        out_of_scope_terms = [
            "hack",
            "bank account",
            "pirated",
            "weapon",
            "malware",
        ]

        if any(term in text for term in crisis_terms):
            return {"label": "L3_CRISIS", "reason": "The message may involve self-harm, violence, or immediate danger."}
        if any(term in text for term in medical_terms):
            return {"label": "L4_MEDICAL", "reason": "The message asks for diagnosis, medication, or clinical treatment guidance."}
        if any(term in text for term in out_of_scope_terms):
            return {"label": "L5_OUT_OF_SCOPE", "reason": "The message is outside student wellbeing or academic support."}
        if any(term in text for term in distress_terms):
            return {"label": "L2_DISTRESS", "reason": "The message suggests strong distress or hopelessness without immediate danger."}
        if any(term in text for term in stress_terms):
            return {"label": "L1_STRESS", "reason": "The message suggests mild stress, worry, nervousness, or pressure."}
        return {"label": "L0_NORMAL", "reason": "The message is normal academic or study-support content."}

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

    def _build_s0_prompt(self, user_message: str) -> str:
        return f"""You are MindBridge Lite, a basic student-support chatbot.
Answer the student's question using general academic support knowledge. Do not use retrieved documents.
Keep the answer practical, concise, and student-friendly.

Student question: {user_message}
"""

    def _build_safety_rag_prompt(
        self,
        user_message: str,
        grouped_context: str,
        risk_label: str,
    ) -> str:
        return f"""You are MindBridge-RAG S2, a safety-aware student wellbeing and academic support assistant.

Risk label: {risk_label}

Use only the retrieved corpus passages below as grounding. If the corpus is incomplete, say what is supported and avoid inventing details.

Safety rules:
- Do not diagnose mental health conditions.
- Do not recommend medication or clinical treatment.
- Do not provide self-harm, violence, or unsafe instructions.
- For distress, encourage trusted human support and campus support.
- Keep the answer calm, practical, and concise.

Retrieved corpus:
{grouped_context}

Student question: {user_message}
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
        display_chunks = self._format_chunks_for_display(chunks)

        if not self.client:
            return {
                "status": "error",
                "response": "MISTRAL_API_KEY is missing in backend/.env",
                "sources": sources,
                "chunks": display_chunks,
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
                "chunks": display_chunks,
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Mistral error: {e}",
                "sources": sources,
                "chunks": display_chunks,
            }

    async def basic_chatbot(
        self,
        user_message: str,
        temperature: float = 0.3,
    ):
        if not self.client:
            return {
                "status": "error",
                "response": "MISTRAL_API_KEY is missing in backend/.env",
                "sources": [],
            }

        try:
            response = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": self._build_s0_prompt(user_message)}],
                temperature=temperature,
            )
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "sources": [],
            }
        except Exception as e:
            return {"status": "error", "response": f"Mistral error: {e}", "sources": []}

    async def corpus_snapshot(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        source_file: str | None = None,
    ):
        chunks, _, grouped_context, _ = await self._retrieve(
            user_message, top_k, similarity_threshold, source_file
        )
        sources = list(set(c["source_file"] for c in chunks))
        return {
            "status": "success",
            "response": grouped_context
            or "No research corpus chunks were retrieved. The shared class corpus can be integrated here later.",
            "sources": sources,
            "chunks": self._format_chunks_for_display(chunks),
        }

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

    async def safety_aware_rag(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        temperature: float = 0.3,
        source_file: str | None = None,
    ):
        risk = self._classify_risk(user_message)
        risk_label = risk["label"]

        if risk_label == "L3_CRISIS":
            return {
                "status": "success",
                "response": (
                    "I am sorry you are dealing with this. This sounds urgent, so please contact immediate human support now: "
                    "call your local emergency number, campus security, or a trusted person who can stay with you. "
                    "If you are in immediate danger, do not wait for a chatbot response."
                ),
                "risk": risk,
                "sources": [],
                "chunks": [],
            }

        if risk_label == "L4_MEDICAL":
            return {
                "status": "success",
                "response": (
                    "I cannot diagnose a mental health condition or recommend medication. "
                    "A qualified clinician, doctor, or campus counseling service is the right place for diagnosis or treatment advice. "
                    "If useful, I can help you organize your concerns into notes to discuss with a professional."
                ),
                "risk": risk,
                "sources": [],
                "chunks": [],
            }

        if risk_label == "L5_OUT_OF_SCOPE":
            return {
                "status": "success",
                "response": "I can help with student wellbeing and academic support, but I cannot help with that request.",
                "risk": risk,
                "sources": [],
                "chunks": [],
            }

        chunks, _, grouped_context, _ = await self._retrieve(
            user_message, top_k, similarity_threshold, source_file
        )
        sources = list(set(c["source_file"] for c in chunks))
        display_chunks = self._format_chunks_for_display(chunks)

        if not self.client:
            return {
                "status": "error",
                "response": "MISTRAL_API_KEY is missing in backend/.env",
                "risk": risk,
                "sources": sources,
                "chunks": display_chunks,
            }

        try:
            response = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": self._build_safety_rag_prompt(
                            user_message,
                            grouped_context or "No retrieved corpus passages.",
                            risk_label,
                        ),
                    }
                ],
                temperature=temperature,
            )
            response_text = response.choices[0].message.content.strip()
            if risk_label == "L2_DISTRESS":
                response_text += (
                    "\n\nPlease also consider telling a trusted person, teacher, "
                    "counselor, or campus support service that you feel overwhelmed."
                )
            return {
                "status": "success",
                "response": response_text,
                "risk": risk,
                "sources": sources,
                "chunks": display_chunks,
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Mistral error: {e}",
                "risk": risk,
                "sources": sources,
                "chunks": display_chunks,
            }

    async def compare_systems(
        self,
        user_message: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        temperature: float = 0.3,
        source_file: str | None = None,
    ):
        async def timed(awaitable):
            started_at = perf_counter()
            result = await awaitable
            result["response_time_seconds"] = round(
                perf_counter() - started_at,
                4,
            )
            return result

        s0_task = timed(self.basic_chatbot(user_message, temperature))
        corpus_task = timed(
            self.corpus_snapshot(
                user_message,
                top_k,
                similarity_threshold,
                source_file,
            )
        )
        s1_task = timed(
            self.chat(
                user_message,
                top_k,
                similarity_threshold,
                temperature,
                source_file,
            )
        )
        s2_task = timed(
            self.safety_aware_rag(
                user_message,
                top_k,
                similarity_threshold,
                temperature,
                source_file,
            )
        )

        s0, corpus, s1, s2 = await asyncio.gather(
            s0_task,
            corpus_task,
            s1_task,
            s2_task,
        )

        s0["metrics"] = self._build_response_metrics(
            user_message,
            s0.get("response", ""),
            s0.get("chunks"),
            status=s0.get("status", "success"),
        )
        corpus["metrics"] = self._build_response_metrics(
            user_message,
            corpus.get("response", ""),
            corpus.get("chunks"),
            status=corpus.get("status", "success"),
        )
        s1["metrics"] = self._build_response_metrics(
            user_message,
            s1.get("response", ""),
            s1.get("chunks"),
            status=s1.get("status", "success"),
        )
        s2["metrics"] = self._build_response_metrics(
            user_message,
            s2.get("response", ""),
            s2.get("chunks"),
            risk=s2.get("risk"),
            status=s2.get("status", "success"),
        )

        return {
            "status": "success",
            "systems": {
                "s0": s0,
                "corpus": corpus,
                "s1": s1,
                "s2": s2,
            },
        }


orchestrator = StudyOrchestrator()
