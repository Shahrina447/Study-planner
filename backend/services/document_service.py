import io
import json
from collections import Counter

import fitz
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from fastapi import UploadFile

from rag.db import db
from rag.in_memory_db import memory_db


class DocumentService:
    async def upload_document(self, file: UploadFile):
        from rag.embedder import embedder

        content = await file.read()
        text = self._extract_text(file.filename, content).replace("\x00", "")
        chunks = self._chunk_text(text)

        chunk_index = 0
        for chunk in chunks:
            chunk = chunk.replace("\x00", "")
            if not chunk.strip():
                continue

            embedding = embedder.embed(chunk)
            await self._store_chunk(file.filename, chunk_index, chunk, embedding)
            chunk_index += 1

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_added": chunk_index,
        }

    async def list_documents(self):
        if db.pool:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT source_file,
                           COUNT(*) AS chunk_count,
                           MAX(created_at) AS indexed_at
                    FROM legal_chunks
                    GROUP BY source_file
                    ORDER BY MAX(created_at) DESC
                    """
                )
                return {
                    "documents": [
                        {
                            "filename": row["source_file"],
                            "chunks": row["chunk_count"],
                            "indexed_at": row["indexed_at"].isoformat()
                            if row["indexed_at"]
                            else None,
                        }
                        for row in rows
                    ]
                }

        counts = Counter(chunk["source_file"] for chunk in memory_db.chunks)
        return {
            "documents": [
                {"filename": name, "chunks": count, "indexed_at": None}
                for name, count in counts.items()
            ]
        }

    async def delete_document(self, filename: str):
        if db.pool:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM legal_chunks WHERE source_file = $1",
                    filename,
                )
            return {"status": "success", "deleted": filename}

        indices_to_keep = [
            index
            for index, chunk in enumerate(memory_db.chunks)
            if chunk["source_file"] != filename
        ]
        memory_db.chunks = [memory_db.chunks[index] for index in indices_to_keep]
        memory_db.embeddings = [
            memory_db.embeddings[index] for index in indices_to_keep
        ]
        return {"status": "success", "deleted": filename}

    def _extract_text(self, filename: str, content: bytes) -> str:
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            return self._extract_pdf_text(content)
        if filename_lower.endswith(".docx"):
            return self._extract_docx_text(content)
        return content.decode("utf-8", errors="ignore")

    def _extract_pdf_text(self, content: bytes) -> str:
        document = fitz.open(stream=content, filetype="pdf")
        return "\n".join(page.get_text() for page in document)

    def _extract_docx_text(self, content: bytes) -> str:
        document = DocxDocument(io.BytesIO(content))
        parts: list[str] = []

        def extract_text_from_element(element) -> str:
            return "".join(node.text or "" for node in element.iter(qn("w:t")))

        for paragraph in document.paragraphs:
            line = paragraph.text.strip()
            if line:
                parts.append(line)

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        parts.append(cell_text)

        for section in document.sections:
            headers_and_footers = [
                section.header,
                section.footer,
                section.even_page_header,
                section.even_page_footer,
                section.first_page_header,
                section.first_page_footer,
            ]
            for header_or_footer in headers_and_footers:
                try:
                    for paragraph in header_or_footer.paragraphs:
                        line = paragraph.text.strip()
                        if line:
                            parts.append(line)
                except Exception:
                    pass

        for text_box in document.element.body.iter(qn("w:txbxContent")):
            raw = extract_text_from_element(text_box).strip()
            if raw:
                parts.append(raw)

        return "\n".join(parts)

    def _chunk_text(self, text: str) -> list[str]:
        chunk_size = 300
        words = text.split()
        return [
            " ".join(words[index : index + chunk_size])
            for index in range(0, len(words), chunk_size)
        ]

    async def _store_chunk(
        self,
        filename: str,
        chunk_index: int,
        content: str,
        embedding: list[float],
    ) -> None:
        if db.pool:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO legal_chunks (source_file, chunk_index, content, embedding, doc_type)
                    VALUES ($1, $2, $3, $4::vector, $5)
                    """,
                    filename,
                    chunk_index,
                    content,
                    json.dumps(embedding),
                    "study_material",
                )
        else:
            memory_db.add_chunk(filename, content, embedding)


document_service = DocumentService()
