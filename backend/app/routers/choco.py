from fastapi import APIRouter, Depends, HTTPException
import json
from app.auth import get_current_user
from app.models import ChocoChatRequest, ChocoChatResponse
from app.rag.pipeline import ChocoAIEngine

router = APIRouter(prefix="/api/choco", tags=["CHOCO Assistant"])

@router.post("/chat", response_model=ChocoChatResponse)
def choco_chat(
    req: ChocoChatRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["ID"]
    session_id = req.session_id or f"user_{user_id}_default"
    
    engine = ChocoAIEngine.get_instance()
    result = engine.chat(
        user_id=user_id,
        session_id=session_id,
        user_message=req.message
    )
    return result

@router.get("/history")
def get_chat_history(
    session_id: str = "default_session",
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["ID"]
    engine = ChocoAIEngine.get_instance()
    rows = engine.get_user_buffer(user_id=user_id, session_id=session_id, limit=20)
    
    formatted = []
    for r in rows:
        cards = []
        if r.get("UI_CARDS_JSON"):
            try:
                cards = json.loads(r["UI_CARDS_JSON"])
            except Exception:
                pass
        formatted.append({
            "role": r["ROLE"],
            "content": r["CONTENT"],
            "ui_cards": cards,
            "created_at": str(r.get("CREATED_AT", ""))
        })
    return {"user_id": user_id, "session_id": session_id, "messages": formatted}

@router.delete("/history")
def clear_chat_history(
    session_id: str = "default_session",
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["ID"]
    engine = ChocoAIEngine.get_instance()
    engine.clear_user_buffer(user_id=user_id, session_id=session_id)
    return {"message": "Isolated conversation buffer cleared successfully."}
