from fastapi import APIRouter
from pydantic import BaseModel

from ai.engine import generate_response
from ai.memory import clear_memory, get_memory
from backend.database.db import (
    list_conversations,
    get_messages,
    get_conversation,
    delete_conversation,
)
from backend.middleware import sanitize_input


router = APIRouter(
    prefix="/api",
    tags=["chat"]
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    intent: str = "unknown"
    model: str = "kairus-core-0.3.0"
    memory: dict = {}
    tool: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Sanitizar input
    clean_message = sanitize_input(request.message)

    result = generate_response(clean_message, request.session_id)

    return ChatResponse(
        response=result["response"],
        intent=result["intent"],
        model=result["model"],
        memory=result.get("memory", {}),
        tool=result.get("tool"),
    )


@router.post("/chat/clear")
async def clear_chat(session_id: str = "default"):
    clear_memory(session_id)
    return {"status": "ok", "message": "Memoria limpa."}


@router.get("/chat/memory")
async def get_chat_memory(session_id: str = "default"):
    memory = get_memory(session_id)
    return {
        "message_count": memory.message_count,
        "user_info": memory.user_info,
        "topics": memory.topics_discussed,
        "recent_messages": memory.get_recent_messages(5),
    }


@router.get("/conversations")
async def get_conversations(limit: int = 20):
    convs = list_conversations(limit)
    return {"conversations": convs}


@router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages(conv_id: str, limit: int = 50):
    msgs = get_messages(conv_id, limit)
    conv = get_conversation(conv_id)
    return {
        "conversation": conv,
        "messages": msgs,
    }


@router.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: str):
    delete_conversation(conv_id)
    clear_memory(conv_id)
    return {"status": "ok", "message": "Conversa deletada."}