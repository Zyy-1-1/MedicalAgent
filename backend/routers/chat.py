from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse, SessionCreate, SessionInfo
from memory import create_session, get_session, add_message, get_history
from agents.chat_agent import handle_chat
from agents.orchestrator import run_diagnosis_pipeline

router = APIRouter()


@router.post("/sessions", response_model=SessionInfo)
async def create_new_session(body: SessionCreate):
    return create_session(body.patient_info)


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(
        session_id=sess["id"],
        created_at=sess["created_at"],
        message_count=len(sess["history"].messages),
        patient_info=sess.get("patient_info"),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    sess = get_session(body.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found. Create a session first.")

    reply = await handle_chat(body.session_id, body.message)

    return ChatResponse(
        session_id=body.session_id,
        reply=reply,
    )
