import uuid
import json
import os
from datetime import datetime
from typing import Optional
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from models import PatientInfo, SessionInfo

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# session_id -> {"info": dict, "history": ChatMessageHistory}
sessions: dict[str, dict] = {}


def create_session(patient_info: Optional[PatientInfo] = None) -> SessionInfo:
    session_id = uuid.uuid4().hex[:12]
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "history": ChatMessageHistory(),
        "patient_info": patient_info.model_dump() if patient_info else None,
    }
    return SessionInfo(
        session_id=session_id,
        created_at=sessions[session_id]["created_at"],
        message_count=0,
        patient_info=patient_info,
    )


def get_session(session_id: str) -> Optional[dict]:
    return sessions.get(session_id)


def add_message(session_id: str, role: str, content: str):
    if session_id not in sessions:
        return
    if role == "user":
        sessions[session_id]["history"].add_user_message(content)
    elif role == "assistant":
        sessions[session_id]["history"].add_ai_message(content)
    _save_session(session_id)


def get_chat_history(session_id: str) -> list[BaseMessage]:
    """返回 LangChain 消息列表，用于 ChatPromptTemplate 的 MessagesPlaceholder。"""
    if session_id in sessions:
        return sessions[session_id]["history"].messages[-10:]
    return []


def get_history(session_id: str) -> list[dict]:
    """返回 dict 格式的历史消息（用于 API 响应等）。"""
    if session_id not in sessions:
        return []
    result = []
    for msg in sessions[session_id]["history"].messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        result.append({"role": role, "content": msg.content})
    return result


def _save_session(session_id: str):
    if session_id not in sessions:
        return
    session_data = sessions[session_id]
    path = os.path.join(DATA_DIR, f"session_{session_id}.json")
    serializable = {
        "id": session_data["id"],
        "created_at": session_data["created_at"],
        "messages": [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in session_data["history"].messages
        ],
        "patient_info": session_data.get("patient_info"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def load_all_sessions():
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("session_") and filename.endswith(".json"):
            path = os.path.join(DATA_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                history = ChatMessageHistory()
                for msg in data.get("messages", []):
                    if msg["role"] == "user":
                        history.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        history.add_ai_message(msg["content"])
                sessions[data["id"]] = {
                    "id": data["id"],
                    "created_at": data.get("created_at", ""),
                    "history": history,
                    "patient_info": data.get("patient_info"),
                }
