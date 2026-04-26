"""
诊断智能体 — AutoGen AssistantAgent

使用 AutoGen 智能体基于患者症状、病史和 GraphRAG 检索的医学知识，
生成鉴别诊断和初步诊断。
"""
import logging
from autogen import AssistantAgent
from agents.base import get_autogen_llm_config, run_agent, parse_json_response
from models import DiagnosisResult

logger = logging.getLogger(__name__)

_DEFAULT = DiagnosisResult(
    primary_diagnosis="信息不足，无法确定",
    differential_diagnoses=[],
    confidence="low",
    reasoning="由于信息不足，无法完成诊断分析。",
)

DIAGNOSIS_SYSTEM = """你是一名医疗诊断AI助手。基于患者症状和医学参考资料，提供鉴别诊断。

输出 JSON，包含以下字段：
- primary_diagnosis: 最可能的初步诊断（中文）
- differential_diagnoses: 其他可能疾病的列表（字符串数组）
- confidence: 置信度，只能是 "low"、"moderate" 或 "high"
- reasoning: 临床推理过程（中文）

重要提示：你是AI助手而非医生。务必声明评估仅为初步判断，患者必须咨询医疗专业人士。
只输出 JSON，不要在 JSON 前后添加任何其他内容。"""

diagnosis_agent = AssistantAgent(
    name="Diagnostician",
    system_message=DIAGNOSIS_SYSTEM,
    llm_config=get_autogen_llm_config(temperature=0.3),
)


def _format_patient_info(patient_info: dict | None) -> str:
    """将患者信息格式化为文本。"""
    if not patient_info:
        return "未提供"
    parts = []
    if patient_info.get("age"):
        parts.append(f"年龄={patient_info['age']}")
    if patient_info.get("gender"):
        parts.append(f"性别={patient_info['gender']}")
    if patient_info.get("medical_history"):
        parts.append(f"既往病史={patient_info['medical_history']}")
    if patient_info.get("current_medications"):
        parts.append(f"当前用药={patient_info['current_medications']}")
    return "；".join(parts) if parts else "未提供"


async def diagnose(symptoms: str, patient_info: dict | None, context: str) -> dict:
    """使用 AutoGen 诊断智能体进行分析。

    Args:
        symptoms: 症状描述
        patient_info: 患者信息字典
        context: GraphRAG 检索的医学知识上下文

    Returns:
        DiagnosisResult 的 model_dump() 字典
    """
    info_text = _format_patient_info(patient_info)
    message = (
        f"患者症状：{symptoms}\n"
        f"患者信息：{info_text}\n"
        f"相关医学参考资料：\n{context or '无相关参考资料'}"
    )

    try:
        reply = await run_agent(diagnosis_agent, message)
        logger.debug(f"Diagnosis agent reply: {reply[:200]}...")
        return parse_json_response(reply, DiagnosisResult, lambda: _DEFAULT)
    except Exception as e:
        logger.warning(f"Diagnosis agent failed: {e}")
        return _DEFAULT.model_dump()
