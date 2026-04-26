from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


# --- Request Models ---

class PatientInfo(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    medical_history: Optional[str] = Field(None, description="Known medical conditions")
    current_medications: Optional[str] = Field(None, description="Current medications")


class SymptomReport(BaseModel):
    symptoms: str = Field(..., description="Patient's symptom description")
    duration: Optional[str] = Field(None, description="How long symptoms have persisted")
    severity_level: Optional[str] = Field(None, description="Self-reported severity")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message / symptom description")
    patient_info: Optional[PatientInfo] = Field(None, description="Patient background info")


class DiagnosisRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    symptoms: str = Field(..., description="Detailed symptom description")
    duration: Optional[str] = Field(None)
    severity_level: Optional[str] = Field(None)
    patient_info: Optional[PatientInfo] = Field(None)


# --- Response Models ---

class TriageResult(BaseModel):
    urgency: Severity = Field(..., description="Urgency level")
    recommended_action: str = Field(..., description="Recommended immediate action")
    specialty: Optional[str] = Field(None, description="Suggested specialist type")


class SymptomAnalysis(BaseModel):
    key_symptoms: list[str] = Field(default_factory=list)
    possible_conditions: list[str] = Field(default_factory=list)
    requires_emergency: bool = Field(False)


class DiagnosisResult(BaseModel):
    primary_diagnosis: str = Field(..., description="Most likely diagnosis")
    differential_diagnoses: list[str] = Field(default_factory=list)
    confidence: str = Field("moderate", description="Confidence level: low/moderate/high")
    reasoning: str = Field("", description="Clinical reasoning")


class TreatmentPlan(BaseModel):
    immediate_actions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    lifestyle_recommendations: list[str] = Field(default_factory=list)
    follow_up: str = Field("", description="Follow-up recommendations")
    disclaimer: str = Field(
        "本内容为AI生成的医疗信息仅供参考，请务必咨询持牌医疗专业人士获取实际诊疗意见。"
    )


class RetrievedDocument(BaseModel):
    content: str
    source: str
    source_cn: str = ""
    type: str = ""
    relevance: float


class ChatResponse(BaseModel):
    session_id: str
    reply: str = Field(..., description="Agent's reply")
    triage: Optional[TriageResult] = None
    symptom_analysis: Optional[SymptomAnalysis] = None
    diagnosis: Optional[DiagnosisResult] = None
    treatment: Optional[TreatmentPlan] = None
    references: list[RetrievedDocument] = Field(default_factory=list)


class DiagnosisResponse(BaseModel):
    session_id: str
    triage: TriageResult
    symptom_analysis: SymptomAnalysis
    diagnosis: DiagnosisResult
    treatment: TreatmentPlan
    references: list[RetrievedDocument] = Field(default_factory=list)


class SessionCreate(BaseModel):
    patient_info: Optional[PatientInfo] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int
    patient_info: Optional[PatientInfo] = None
