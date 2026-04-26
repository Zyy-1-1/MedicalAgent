"""
治疗建议智能体 — AutoGen AssistantAgent

使用 AutoGen 智能体基于诊断结果和患者情况，推荐治疗计划，
包括紧急措施、用药参考、生活方式建议和随访计划。
"""
import logging
from autogen import AssistantAgent
from agents.base import get_autogen_llm_config, run_agent, parse_json_response
from models import TreatmentPlan

logger = logging.getLogger(__name__)

_DEFAULT = TreatmentPlan(
    immediate_actions=["请咨询医疗专业人士进行适当评估。"],
    medications=[],
    lifestyle_recommendations=["保持健康饮食和充足水分摄入。"],
    follow_up="请预约您的初级保健医生进行进一步检查。",
    disclaimer="本内容为AI生成的医疗信息仅供参考，请务必咨询持牌医疗专业人士获取实际诊疗意见。",
)

TREATMENT_SYSTEM = """你是一名医疗治疗建议AI助手。基于诊断结果和患者情况，提供治疗计划建议。

输出 JSON，包含以下字段：
- immediate_actions: 患者应立即采取的措施列表（字符串数组）
- medications: 可能的用药方案列表，仅通用药名，不要指定具体剂量（字符串数组）
- lifestyle_recommendations: 生活方式建议列表（字符串数组）
- follow_up: 随访建议（字符串）

重要：务必声明此为AI生成信息，不是医疗建议。不要处方管制类药物。
只输出 JSON，不要在 JSON 前后添加任何其他内容。"""

treatment_agent = AssistantAgent(
    name="TreatmentAdvisor",
    system_message=TREATMENT_SYSTEM,
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


async def recommend(
    diagnosis: str,
    symptoms: str,
    patient_info: dict | None,
    context: str,
) -> dict:
    """使用 AutoGen 治疗建议智能体生成治疗计划。

    Args:
        diagnosis: 初步诊断结果
        symptoms: 症状描述
        patient_info: 患者信息字典
        context: GraphRAG 检索的医学知识上下文

    Returns:
        TreatmentPlan 的 model_dump() 字典
    """
    info_text = _format_patient_info(patient_info)
    message = (
        f"诊断：{diagnosis}\n"
        f"症状：{symptoms}\n"
        f"患者信息：{info_text}\n"
        f"相关参考资料：\n{context or '无相关参考资料'}"
    )

    try:
        reply = await run_agent(treatment_agent, message)
        logger.debug(f"Treatment agent reply: {reply[:200]}...")
        return parse_json_response(reply, TreatmentPlan, lambda: _DEFAULT)
    except Exception as e:
        logger.warning(f"Treatment agent failed: {e}")
        return _DEFAULT.model_dump()
