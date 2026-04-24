import logging
from models import PatientInfo, TriageResult, SymptomAnalysis, DiagnosisResult, TreatmentPlan, RetrievedDocument
from agents.triage import triage
from agents.symptom_analyzer import analyze
from agents.diagnosis import diagnose
from agents.treatment import recommend
from rag import retriever
from memory import add_message

logger = logging.getLogger(__name__)


async def run_diagnosis_pipeline(
    session_id: str,
    symptoms: str,
    duration: str = "",
    severity: str = "",
    patient_info: PatientInfo | None = None,
) -> dict:
    """Run the full multi-agent diagnosis pipeline."""

    add_message(session_id, "user", symptoms)
    patient_dict = patient_info.model_dump() if patient_info else None

    # Step 1: Triage
    logger.info(f"[{session_id}] Running triage...")
    triage_data = triage(symptoms, duration, severity)
    triage_result = TriageResult(**triage_data)
    logger.info(f"[{session_id}] Triage urgency: {triage_result.urgency}")

    # Step 2: Symptom Analysis
    logger.info(f"[{session_id}] Analyzing symptoms...")
    analysis_data = analyze(symptoms, duration, severity)
    symptom_analysis = SymptomAnalysis(**analysis_data)
    logger.info(f"[{session_id}] Key symptoms: {symptom_analysis.key_symptoms}")

    # Step 3: RAG Retrieval
    logger.info(f"[{session_id}] Retrieving medical knowledge...")
    retrieved_docs = retriever.retrieve(symptoms, top_k=3)
    context = retriever.get_context(symptoms, top_k=3)
    references = [
        RetrievedDocument(content=d["content"], source=d["source"], relevance=d["relevance"])
        for d in retrieved_docs
    ]
    logger.info(f"[{session_id}] Retrieved {len(references)} references")

    # Step 4: Diagnosis
    logger.info(f"[{session_id}] Generating diagnosis...")
    diagnosis_data = diagnose(symptoms, patient_dict, context)
    diagnosis_result = DiagnosisResult(**diagnosis_data)
    logger.info(f"[{session_id}] Primary diagnosis: {diagnosis_result.primary_diagnosis}")

    # Step 5: Treatment Recommendation
    logger.info(f"[{session_id}] Generating treatment plan...")
    treatment_data = recommend(
        diagnosis_result.primary_diagnosis,
        symptoms,
        patient_dict,
        context,
    )
    treatment_plan = TreatmentPlan(**treatment_data)

    # Compile the response
    response_text = _compile_response(
        triage_result, symptom_analysis, diagnosis_result, treatment_plan
    )
    add_message(session_id, "assistant", response_text)

    return {
        "triage": triage_result,
        "symptom_analysis": symptom_analysis,
        "diagnosis": diagnosis_result,
        "treatment": treatment_plan,
        "reply": response_text,
        "references": references,
    }


def _compile_response(
    triage: TriageResult,
    analysis: SymptomAnalysis,
    diagnosis: DiagnosisResult,
    treatment: TreatmentPlan,
) -> str:
    parts = []

    urgency_emoji = {
        "low": "🟢", "medium": "🟡", "high": "🟠", "emergency": "🔴"
    }

    urgency_label = {
        "low": "低风险", "medium": "中等风险", "high": "高风险", "emergency": "紧急"
    }

    confidence_label = {
        "low": "低", "moderate": "中等", "high": "高"
    }

    urg = triage.urgency.value if hasattr(triage.urgency, 'value') else str(triage.urgency)
    parts.append(f"## 分诊评估\n\n{urgency_emoji.get(urg, '')} **紧急程度：{urgency_label.get(urg, urg)}**")
    parts.append(f"\n**建议措施：**{triage.recommended_action}")
    if triage.specialty:
        parts.append(f"\n**建议科室：**{triage.specialty}")

    parts.append(f"\n\n## 症状分析\n\n**关键症状：**{', '.join(analysis.key_symptoms)}")
    parts.append(f"\n**可能的疾病：**{', '.join(analysis.possible_conditions)}")
    if analysis.requires_emergency:
        parts.append("\n⚠️ **警告：检测到紧急症状指标，请立即就医！**")

    parts.append(f"\n\n## 诊断\n\n**初步诊断：**{diagnosis.primary_diagnosis}")
    conf = diagnosis.confidence
    parts.append(f"\n**置信度：**{confidence_label.get(conf, conf)}")
    if diagnosis.differential_diagnoses:
        parts.append(f"\n**鉴别诊断：**{', '.join(diagnosis.differential_diagnoses)}")
    parts.append(f"\n**推理依据：**{diagnosis.reasoning}")

    parts.append(f"\n\n## 治疗建议\n\n**紧急措施：**")
    for action in treatment.immediate_actions:
        parts.append(f"- {action}")
    if treatment.medications:
        parts.append(f"\n**参考用药：**{', '.join(treatment.medications)}")
    if treatment.lifestyle_recommendations:
        parts.append(f"\n**生活方式建议：**")
        for rec in treatment.lifestyle_recommendations:
            parts.append(f"- {rec}")
    parts.append(f"\n**随访建议：**{treatment.follow_up}")
    parts.append(f"\n\n---\n*{treatment.disclaimer}*")

    return "\n".join(parts)
