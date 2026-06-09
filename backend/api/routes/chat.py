from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest, ConversationUpdateRequest, SystemCompareRequest
from rag.db import db
from services.orchestrator import orchestrator


router = APIRouter()


@router.get("/conversations")
async def list_conversations():
    return {"conversations": await db.list_conversations()}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdateRequest,
):
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Conversation title is required.")
    conversation = await db.update_conversation(conversation_id, title[:120])
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    deleted = await db.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "success", "deleted": conversation_id}


@router.post("/chat")
async def chat_with_notes(request: ChatRequest):
    kwargs = {
        "top_k": request.top_k,
        "similarity_threshold": request.similarity_threshold,
        "temperature": request.temperature,
        "source_file": request.source_file,
    }
    if request.mode == "corpus":
        result = await orchestrator.corpus_only(request.message, **kwargs)
    elif request.mode == "compare":
        result = await orchestrator.compare(request.message, **kwargs)
    else:
        result = await orchestrator.chat(request.message, **kwargs)

    conversation_id = await db.record_exchange(
        request.message,
        result,
        request.mode,
        request.conversation_id,
    )
    if conversation_id is not None:
        result["conversation_id"] = conversation_id
    return result


@router.post("/chat/compare-systems")
async def compare_chatbot_systems(request: SystemCompareRequest):
    result = await orchestrator.compare_systems(
        user_message=request.message,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        temperature=request.temperature,
        source_file=request.source_file,
    )
    conversation_id = await db.record_exchange(
        request.message,
        result,
        "compare_systems",
        request.conversation_id,
    )
    if conversation_id is not None:
        result["conversation_id"] = conversation_id
    return result
