import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai.engine import generate_response, stream_response
from ai.memory import clear_memory, get_memory
from backend.database.db import (
    list_conversations,
    get_messages,
    get_conversation,
    delete_conversation,
    create_conversation,
)
from backend.middleware import sanitize_input
from backend.auth import get_current_user


router = APIRouter(
    prefix="/api",
    tags=["chat"]
)


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    intent: str = "unknown"
    model: str = "kairus-core-0.3.0"
    memory: dict = {}
    tool: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    # Verifica se a conversa pertence ao usuario
    conv = get_conversation(request.session_id)
    if conv and conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    # Cria conversa se nao existir
    if not conv:
        create_conversation(request.session_id, current_user["user_id"])
    
    clean_message = sanitize_input(request.message)
    result = generate_response(clean_message, request.session_id)

    return ChatResponse(
        response=result["response"],
        intent=result["intent"],
        model=result["model"],
        memory=result.get("memory", {}),
        tool=result.get("tool"),
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de streaming: resposta em tempo real via SSE."""
    conv = get_conversation(request.session_id)
    if conv and conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    if not conv:
        create_conversation(request.session_id, current_user["user_id"])
    
    clean_message = sanitize_input(request.message)

    def event_generator():
        for event in stream_response(clean_message, request.session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/clear")
async def clear_chat(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    conv = get_conversation(session_id)
    if conv and conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    clear_memory(session_id)
    return {"status": "ok", "message": "Memoria limpa."}


@router.get("/chat/memory")
async def get_chat_memory(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    conv = get_conversation(session_id)
    if conv and conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    memory = get_memory(session_id)
    return {
        "message_count": memory.message_count,
        "user_info": memory.user_info,
        "topics": memory.topics_discussed,
        "recent_messages": memory.get_recent_messages(5),
    }


@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    convs = list_conversations(current_user["user_id"], limit)
    return {"conversations": convs}


@router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa nao encontrada"
        )
    
    if conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    msgs = get_messages(conv_id, limit)
    return {
        "conversation": conv,
        "messages": msgs,
    }


@router.delete("/conversations/{conv_id}")
async def delete_conv(
    conv_id: str,
    current_user: dict = Depends(get_current_user)
):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa nao encontrada"
        )
    
    if conv["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversa nao pertence a este usuario"
        )
    
    delete_conversation(conv_id)
    clear_memory(conv_id)
    return {"status": "ok", "message": "Conversa deletada."}