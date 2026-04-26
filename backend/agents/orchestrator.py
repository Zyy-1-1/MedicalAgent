import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from models import PatientInfo, TriageResult, SymptomAnalysis, DiagnosisResult, TreatmentPlan, RetrievedDocument
from memory import add_message

logger = logging.getLogger(__name__)


class DiagnosisState(TypedDict):
    """LangGraph 诊断流程状态。"""
    session_id: str
    symptoms: str
    duration: str
    severity: str
    patient_info: Optional[dict]

    # 各节点输出
    triage_result: Optional[dict]
    symptom_analysis: Optional[dict]
    rag_context: str
    rag_docs: list[dict]
    diagnosis_result: Optional[dict]
    treatment_plan: Optional[dict]

    # 最终输出
    reply: str
    references: list


def _triage_node(state: DiagnosisState) -> dict:
    from agents.triage import triage
    logger.info(f"[{state['session_id']}] Running triage...")
    result = triage(state["symptoms"], state["duration"], state["severity"])
    logger.info(f"[{state['session_id']}] Triage urgency: {result.get('urgency')}")
    return {"triage_result": result}


def _symptom_analysis_node(state: DiagnosisState) -> dict:
    from agents.symptom_analyzer import analyze
    logger.info(f"[{state['session_id']}] Analyzing symptoms...")
    result = analyze(state["symptoms"], state["duration"], state["severity"])
    logger.info(f"[{state['session_id']}] Key symptoms: {result.get('key_symptoms')}")
    return {"symptom_analysis": result}


def _rag_retrieval_node(state: DiagnosisState) -> dict:
    from rag import retriever
    logger.info(f"[{state['session_id']}] Retrieving medical knowledge...")
    docs = retriever.retrieve(state["symptoms"], top_k=3)
    context = retriever.get_context(state["symptoms"], top_k=3)
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
    logger.info(f"[{state['session_id']}] Retrieved {len(references)} references")
    return {"rag_context": context, "rag_docs": docs, "references": references}


def _diagnosis_node(state: DiagnosisState) -> dict:
    from agents.diagnosis import diagnose
    logger.info(f"[{state['session_id']}] Generating diagnosis...")
    result = diagnose(state["symptoms"], state["patient_info"], state["rag_context"])
    logger.info(f"[{state['session_id']}] Primary diagnosis: {result.get('primary_diagnosis')}")
    return {"diagnosis_result": result}


def _treatment_node(state: DiagnosisState) -> dict:
    from agents.treatment import recommend
    logger.info(f"[{state['session_id']}] Generating treatment plan...")
    result = recommend(
        state["diagnosis_result"]["primary_diagnosis"],
        state["symptoms"],
        state["patient_info"],
        state["rag_context"],
    )
    return {"treatment_plan": result}


def _compile_response_node(state: DiagnosisState) -> dict:
    reply = _compile_response(
        triage=TriageResult(**state["triage_result"]),
        analysis=SymptomAnalysis(**state["symptom_analysis"]),
        diagnosis=DiagnosisResult(**state["diagnosis_result"]),
        treatment=TreatmentPlan(**state["treatment_plan"]),
    )
    return {"reply": reply}


def _compile_response(
    triage: TriageResult,
    analysis: SymptomAnalysis,
    diagnosis: DiagnosisResult,
    treatment: TreatmentPlan,
) -> str:
    parts = []

    urgency_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "emergency": "🔴"}
    urgency_label = {"low": "低风险", "medium": "中等风险", "high": "高风险", "emergency": "紧急"}
    confidence_label = {"low": "低", "moderate": "中等", "high": "高"}

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


def _build_diagnosis_graph():
    """构建 LangGraph 诊断流程。

    流程：do_triage → do_analysis → do_retrieval → do_diagnosis → do_treatment → do_compile → END
    """
    graph = StateGraph(DiagnosisState)

    # 注册节点（名称不能与状态字段名重复）
    graph.add_node("do_triage", _triage_node)
    graph.add_node("do_analysis", _symptom_analysis_node)
    graph.add_node("do_retrieval", _rag_retrieval_node)
    graph.add_node("do_diagnosis", _diagnosis_node)
    graph.add_node("do_treatment", _treatment_node)
    graph.add_node("do_compile", _compile_response_node)

    # 设置流程
    graph.set_entry_point("do_triage")
    graph.add_edge("do_triage", "do_analysis")
    graph.add_edge("do_analysis", "do_retrieval")
    graph.add_edge("do_retrieval", "do_diagnosis")
    graph.add_edge("do_diagnosis", "do_treatment")
    graph.add_edge("do_treatment", "do_compile")
    graph.add_edge("do_compile", END)

    return graph.compile()


# 编译一次，全局复用
_diagnosis_app = _build_diagnosis_graph()


async def run_diagnosis_pipeline(
    session_id: str,
    symptoms: str,
    duration: str = "",
    severity: str = "",
    patient_info: PatientInfo | None = None,
) -> dict:
    """使用 LangGraph 运行多智能体诊断流程。"""

    add_message(session_id, "user", symptoms)
    patient_dict = patient_info.model_dump() if patient_info else None

    initial_state: DiagnosisState = {
        "session_id": session_id,
        "symptoms": symptoms,
        "duration": duration or "",
        "severity": severity or "",
        "patient_info": patient_dict,
        "triage_result": None,
        "symptom_analysis": None,
        "rag_context": "",
        "rag_docs": [],
        "diagnosis_result": None,
        "treatment_plan": None,
        "reply": "",
        "references": [],
    }

    result = _diagnosis_app.invoke(initial_state)

    add_message(session_id, "assistant", result["reply"])

    return {
        "triage": TriageResult(**result["triage_result"]),
        "symptom_analysis": SymptomAnalysis(**result["symptom_analysis"]),
        "diagnosis": DiagnosisResult(**result["diagnosis_result"]),
        "treatment": TreatmentPlan(**result["treatment_plan"]),
        "reply": result["reply"],
        "references": [RetrievedDocument(**r) for r in result["references"]],
    }
