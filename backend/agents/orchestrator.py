"""
多智能体诊断编排器 — AutoGen 顺序流水线

使用 AutoGen AssistantAgent 按顺序执行 5 个步骤（分诊 → 症状分析 → GraphRAG 检索
→ 诊断 → 治疗建议），最后编译为结构化结果。替代原有的 LangGraph StateGraph。
"""
import logging
from typing import Optional
from models import (
    PatientInfo,
    TriageResult,
    SymptomAnalysis,
    DiagnosisResult,
    TreatmentPlan,
    RetrievedDocument,
)
from memory import add_message
from agents.triage import triage
from agents.symptom_analyzer import analyze
from agents.diagnosis import diagnose
from agents.treatment import recommend

logger = logging.getLogger(__name__)

# ── 紧急程度映射 ──
_URGENCY_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🟠", "emergency": "🔴"}
_URGENCY_LABEL = {"low": "低风险", "medium": "中等风险", "high": "高风险", "emergency": "紧急"}
_CONFIDENCE_LABEL = {"low": "低", "moderate": "中等", "high": "高"}


def _compile_response(
    triage_result: TriageResult,
    analysis: SymptomAnalysis,
    diagnosis: DiagnosisResult,
    treatment: TreatmentPlan,
) -> str:
    """将 4 个结构化结果编译为 Markdown 回复文本。"""
    parts = []

    urg = triage_result.urgency.value if hasattr(triage_result.urgency, "value") else str(triage_result.urgency)
    parts.append(f"## 分诊评估\n\n{_URGENCY_EMOJI.get(urg, '')} **紧急程度：{_URGENCY_LABEL.get(urg, urg)}**")
    parts.append(f"\n**建议措施：**{triage_result.recommended_action}")
    if triage_result.specialty:
        parts.append(f"\n**建议科室：**{triage_result.specialty}")

    parts.append(f"\n\n## 症状分析\n\n**关键症状：**{', '.join(analysis.key_symptoms)}")
    parts.append(f"\n**可能的疾病：**{', '.join(analysis.possible_conditions)}")
    if analysis.requires_emergency:
        parts.append("\n⚠️ **警告：检测到紧急症状指标，请立即就医！**")

    parts.append(f"\n\n## 诊断\n\n**初步诊断：**{diagnosis.primary_diagnosis}")
    conf = diagnosis.confidence
    parts.append(f"\n**置信度：**{_CONFIDENCE_LABEL.get(conf, conf)}")
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


async def run_diagnosis_pipeline(
    session_id: str,
    symptoms: str,
    duration: str = "",
    severity: str = "",
    patient_info: Optional[PatientInfo] = None,
) -> dict:
    """运行多智能体诊断流水线（AutoGen 顺序执行，无 LangGraph）。

    执行顺序：
    1. 分诊评估（AutoGen AssistantAgent #1）
    2. 症状分析（AutoGen AssistantAgent #2）
    3. GraphRAG 医学知识检索（图遍历，非 LLM）
    4. 诊断推理（AutoGen AssistantAgent #3）
    5. 治疗建议（AutoGen AssistantAgent #4）
    6. 编译响应（纯 Python）
    """
    logger.info(f"[{session_id}] 诊断流水线启动")

    # 0. 记录用户输入到临时内存
    add_message(session_id, "user", symptoms)

    patient_dict = patient_info.model_dump() if patient_info else None

    # ── 第 1 步：分诊评估 ──
    logger.info(f"[{session_id}] Step 1/5: Triage")
    triage_result_dict = await triage(symptoms, duration, severity)
    triage_result = TriageResult(**triage_result_dict)
    logger.info(f"[{session_id}] 紧急程度: {triage_result.urgency}")

    # ── 第 2 步：症状分析 ──
    logger.info(f"[{session_id}] Step 2/5: Symptom Analysis")
    analysis_dict = await analyze(symptoms, duration, severity)
    analysis = SymptomAnalysis(**analysis_dict)
    logger.info(f"[{session_id}] 关键症状: {analysis.key_symptoms}")

    # ── 第 3 步：GraphRAG 知识图谱检索 ──
    logger.info(f"[{session_id}] Step 3/5: GraphRAG Retrieval")
    from rag import retriever

    docs = retriever.retrieve(symptoms, top_k=3)
    rag_context = retriever.get_context(symptoms, top_k=3)
    references = [
        RetrievedDocument(
            content=d["content"],
            source=d["source"],
            source_cn=d.get("source_cn", ""),
            type=d.get("type", ""),
            relevance=d["relevance"],
        ).model_dump()
        for d in docs
    ]
    logger.info(f"[{session_id}] 检索到 {len(references)} 条医学知识")

    # ── 第 4 步：诊断推理 ──
    logger.info(f"[{session_id}] Step 4/5: Diagnosis")
    diagnosis_dict = await diagnose(symptoms, patient_dict, rag_context)
    diagnosis = DiagnosisResult(**diagnosis_dict)
    logger.info(f"[{session_id}] 初步诊断: {diagnosis.primary_diagnosis}")

    # ── 第 5 步：治疗建议 ──
    logger.info(f"[{session_id}] Step 5/5: Treatment Recommendation")
    treatment_dict = await recommend(
        diagnosis.primary_diagnosis,
        symptoms,
        patient_dict,
        rag_context,
    )
    treatment = TreatmentPlan(**treatment_dict)

    # ── 第 6 步：编译响应 ──
    logger.info(f"[{session_id}] Compiling response")
    reply = _compile_response(triage_result, analysis, diagnosis, treatment)

    # 记录 AI 回复到临时内存
    add_message(session_id, "assistant", reply)

    logger.info(f"[{session_id}] 诊断流水线完成")

    return {
        "triage": triage_result,
        "symptom_analysis": analysis,
        "diagnosis": diagnosis,
        "treatment": treatment,
        "reply": reply,
        "references": [RetrievedDocument(**r) for r in references],
    }
