from fastapi import APIRouter

from api.schemas import ChatRequest
from services.orchestrator import orchestrator


router = APIRouter()


@router.post("/chat")
async def chat_with_notes(request: ChatRequest):
    kwargs = {
        "top_k": request.top_k,
        "similarity_threshold": request.similarity_threshold,
        "temperature": request.temperature,
        "source_file": request.source_file,
    }
    if request.mode == "corpus":
        return await orchestrator.corpus_only(request.message, **kwargs)
    if request.mode == "compare":
        return await orchestrator.compare(request.message, **kwargs)
    return await orchestrator.chat(request.message, **kwargs)
