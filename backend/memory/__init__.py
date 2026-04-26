"""
临时内存会话管理（无文件持久化）

所有会话数据仅保存在内存中，应用重启后自动清除。
"""
import uuid
from datetime import datetime
from typing import Optional
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from models import PatientInfo, SessionInfo

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
