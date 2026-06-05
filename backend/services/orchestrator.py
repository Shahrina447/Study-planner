import re
from mistralai.client import Mistral
from config import settings
from rag.retriever import retriever

class StudyOrchestrator:
    def __init__(self):
        if settings.MISTRAL_API_KEY:
            self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        else:
            self.client = None

    def _clean_text(self, text: str) -> str:
        """
        Normalise raw PDF-extracted text into clean paragraph prose.
        - Remove lines that are just numbers, page markers, or very short noise
        - Collapse mid-sentence line breaks
        - Preserve intentional paragraph breaks
        """
        # Normalise line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into paragraphs on blank lines
        paragraphs = re.split(r"\n{2,}", text)
        cleaned = []
        for para in paragraphs:
            lines = [l.strip() for l in para.split("\n") if l.strip()]
            # Filter out noise lines: pure numbers, single chars, page markers
            lines = [
                l for l in lines
                if not re.fullmatch(r"[\d\s\-–—|/\\]+", l)   # lines that are only digits/symbols
                and len(l) > 3                                  # too short to be content
            ]
            if not lines:
                continue
            # Join lines into flowing prose
            joined = ""
            for line in lines:
                if joined and joined[-1] not in ".!?:;,\"')}]":
                    joined += " " + line
                else:
                    joined = (joined + " " + line).strip() if joined else line
            if joined:
                cleaned.append(joined)
        return "\n\n".join(cleaned)


    def _build_prompt(self, user_message: str, context_text: str) -> str:
        return f"""You are a study planner and teaching assistant. 
Based on the student's uploaded documents (provided below), you have two main tasks:

1. Answer Questions: If the student asks a question about the content, answer it accurately and completely using ONLY the provided study notes. If the notes do not contain the answer, say "I cannot find this in your uploaded study materials."
2. Create Study Plans: If the student asks for a study plan, create a personalized weekly study plan. 
   Rules for Study Plans:
   - Extract all topics and subtopics from the syllabus/document chunks provided.
   - Estimate study time per topic based on content length and complexity.
   - Distribute topics across available days before the exam date.
   - Flag topics with weak quiz scores (if mentioned) as high priority.
   - Output format for study plans:
     Day 1: Topic — [name], Duration — [X hours], Priority — [High/Medium/Low]
     Day 2: ...

Uploaded Documents / Study Notes:
{context_text}

Student Request/Question: {user_message}
"""

    async def chat(self, user_message: str, top_k: int = 5, similarity_threshold: float = 0.0, temperature: float = 0.3, source_file: str | None = None):
        context_chunks = await retriever.search(user_message, top_k=top_k, similarity_threshold=similarity_threshold, source_file=source_file)
        context_text = "\n\n".join([f"Source: {c['source_file']}\nContent: {c['content']}" for c in context_chunks])
        sources = list(set(c['source_file'] for c in context_chunks))

        if not self.client:
            return {
                "status": "error",
                "response": "MISTRAL_API_KEY is missing in backend/.env file.",
                "sources": sources
            }

        try:
            response = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": self._build_prompt(user_message, context_text)}],
                temperature=temperature,
            )
            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "sources": sources
            }
        except Exception as e:
            return {"status": "error", "response": f"Error calling Mistral: {e}"}

    async def corpus_only(self, user_message: str, top_k: int = 5, similarity_threshold: float = 0.0, temperature: float = 0.3, source_file: str | None = None):
        """Synthesise a single unified answer from all retrieved chunks, with inline source citations."""
        context_chunks = await retriever.search(user_message, top_k=top_k, similarity_threshold=similarity_threshold, source_file=source_file)
        sources = list(set(c['source_file'] for c in context_chunks))

        if not context_chunks:
            return {
                "status": "success",
                "response": "No relevant passages found in your uploaded documents for this query.",
                "sources": [],
                "chunks": []
            }

        # Build a clean context block grouping content by source
        source_groups: dict[str, list[str]] = {}
        for chunk in context_chunks:
            src = chunk["source_file"]
            cleaned = self._clean_text(chunk["content"])
            if cleaned:
                source_groups.setdefault(src, []).append(cleaned)

        context_text = "\n\n".join([
            f"[{src}]\n" + " ".join(passages)
            for src, passages in source_groups.items()
        ])

        if not self.client:
            # Fallback: return cleaned grouped text without AI
            return {
                "status": "success",
                "response": context_text,
                "sources": sources,
                "chunks": []
            }

        prompt = (
            f"You are a study assistant. A student asked:\n\"{user_message}\"\n\n"
            f"Below are relevant passages extracted from their study documents, labelled by source file.\n\n"
            f"{context_text}\n\n"
            f"Write a well-structured, easy-to-read answer using Markdown formatting:\n"
            f"- Start with a short **bold summary** (1-2 sentences) of the main answer\n"
            f"- Use `##` headings to break the answer into logical sections\n"
            f"- Use bullet points (`-`) or numbered lists for steps, features, or enumerated items\n"
            f"- Use **bold** to highlight key terms or important concepts\n"
            f"- Cite the source file inline in parentheses when you use information from it, e.g. (make-a-7-day-study-plan.pdf)\n"
            f"- End with a `## Summary` section recapping the key points in 2-3 bullet points\n"
            f"- Do NOT use headings like 'Chunk 1' or 'From PDF X'\n"
            f"- Only use information present in the passages — do not add outside knowledge\n"
        )

        try:
            response = await self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            answer = response.choices[0].message.content.strip()

            # Still return chunk data for the compare view, but cleaned
            formatted_chunks = []
            for i, chunk in enumerate(context_chunks, 1):
                similarity = chunk.get("similarity", None)
                formatted_chunks.append({
                    "index": i,
                    "source": chunk["source_file"],
                    "content": self._clean_text(chunk["content"]),
                    "similarity": round(float(similarity), 4) if similarity is not None else None,
                })

            return {
                "status": "success",
                "response": answer,
                "sources": sources,
                "chunks": formatted_chunks,
            }
        except Exception as e:
            return {"status": "error", "response": f"Error calling Mistral: {e}", "sources": sources, "chunks": []}

    async def compare(self, user_message: str, top_k: int = 5, similarity_threshold: float = 0.0, temperature: float = 0.3, source_file: str | None = None):
        """Return both AI-synthesized response and corpus-synthesised answer side by side."""
        context_chunks = await retriever.search(user_message, top_k=top_k, similarity_threshold=similarity_threshold, source_file=source_file)
        context_text = "\n\n".join([f"Source: {c['source_file']}\nContent: {c['content']}" for c in context_chunks])
        sources = list(set(c['source_file'] for c in context_chunks))

        # Build grouped context for corpus synthesis
        source_groups: dict[str, list[str]] = {}
        for chunk in context_chunks:
            src = chunk["source_file"]
            cleaned = self._clean_text(chunk["content"])
            if cleaned:
                source_groups.setdefault(src, []).append(cleaned)

        grouped_context = "\n\n".join([
            f"[{src}]\n" + " ".join(passages)
            for src, passages in source_groups.items()
        ])

        corpus_prompt = (
            f"You are a study assistant. A student asked:\n\"{user_message}\"\n\n"
            f"Below are relevant passages extracted from their study documents, labelled by source file.\n\n"
            f"{grouped_context}\n\n"
            f"Write a well-structured, easy-to-read answer using Markdown formatting:\n"
            f"- Start with a short **bold summary** (1-2 sentences) of the main answer\n"
            f"- Use `##` headings to break the answer into logical sections\n"
            f"- Use bullet points (`-`) or numbered lists for steps, features, or enumerated items\n"
            f"- Use **bold** to highlight key terms or important concepts\n"
            f"- Cite the source file inline in parentheses when you use information from it, e.g. (StudyPlan_v7.pdf)\n"
            f"- End with a `## Summary` section recapping the key points in 2-3 bullet points\n"
            f"- Do NOT use headings like 'Chunk 1' or 'From PDF X'\n"
            f"- Only use information present in the passages.\n"
        )

        # Formatted chunks for the collapsible detail view
        formatted_chunks = []
        for i, chunk in enumerate(context_chunks, 1):
            similarity = chunk.get("similarity", None)
            formatted_chunks.append({
                "index": i,
                "source": chunk["source_file"],
                "content": self._clean_text(chunk["content"]),
                "similarity": round(float(similarity), 4) if similarity is not None else None,
            })

        if not self.client:
            return {
                "status": "error",
                "ai_response": "MISTRAL_API_KEY is missing in backend/.env file.",
                "corpus_response": grouped_context,
                "sources": sources,
                "chunks": formatted_chunks
            }

        try:
            import asyncio
            ai_task = self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": self._build_prompt(user_message, context_text)}],
                temperature=temperature,
            )
            corpus_task = self.client.chat.complete_async(
                model=settings.MISTRAL_MODEL,
                messages=[{"role": "user", "content": corpus_prompt}],
                temperature=temperature,
            )
            ai_resp, corpus_resp = await asyncio.gather(ai_task, corpus_task)
            return {
                "status": "success",
                "ai_response": ai_resp.choices[0].message.content,
                "corpus_response": corpus_resp.choices[0].message.content.strip(),
                "sources": sources,
                "chunks": formatted_chunks
            }
        except Exception as e:
            return {
                "status": "error",
                "ai_response": f"Error calling Mistral: {e}",
                "corpus_response": grouped_context,
                "sources": sources,
                "chunks": formatted_chunks
            }

orchestrator = StudyOrchestrator()
