import json
import os
from typing import Optional
from models import PatientInfo

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "patient_histories.json")


def _load_histories() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_histories(data: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_patient_history(patient_id: str, session_id: str, diagnosis: dict):
    data = _load_histories()
    if patient_id not in data:
        data[patient_id] = {"sessions": []}
    data[patient_id]["sessions"].append({
        "session_id": session_id,
        "diagnosis": diagnosis,
    })
    _save_histories(data)


def get_patient_history(patient_id: str) -> Optional[dict]:
    data = _load_histories()
    return data.get(patient_id)


def create_patient_id(session_id: str, patient_info: Optional[PatientInfo]) -> str:
    if patient_info:
        parts = [
            str(patient_info.age or ""),
            patient_info.gender or "",
        ]
        return f"P{hash(''.join(parts) + session_id) % 1000000:06d}"
    return f"P{session_id[:6]}"
