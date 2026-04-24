import uuid
import json
import os
from datetime import datetime
from typing import Optional
from models import PatientInfo, SessionInfo

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

sessions: dict[str, dict] = {}


def create_session(patient_info: Optional[PatientInfo] = None) -> SessionInfo:
    session_id = uuid.uuid4().hex[:12]
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
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
    if session_id in sessions:
        sessions[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        _save_session(session_id)


def get_history(session_id: str) -> list[dict]:
    if session_id in sessions:
        return sessions[session_id]["messages"]
    return []


def _save_session(session_id: str):
    path = os.path.join(DATA_DIR, f"session_{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions[session_id], f, ensure_ascii=False, indent=2)


def load_all_sessions():
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("session_") and filename.endswith(".json"):
            path = os.path.join(DATA_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions[data["id"]] = data
