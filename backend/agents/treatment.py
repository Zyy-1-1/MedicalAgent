import logging
from langchain_core.prompts import ChatPromptTemplate
from agents.base import get_llm, get_parser
from models import TreatmentPlan

logger = logging.getLogger(__name__)

_parser = get_parser(TreatmentPlan)

TREATMENT_SYSTEM = """你是一名医疗治疗建议AI助手。基于诊断结果，提供治疗计划建议。

根据诊断和患者情况，提供：
1. 患者应立即采取的措施
2. 可能的用药方案（仅通用药名；不要指定具体剂量）
3. 生活方式建议
4. 随访建议

重要：务必声明此为AI生成信息，不是医疗建议。不要处方管制类药物。建议患者在服用任何药物前咨询医生。"""

TREATMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TREATMENT_SYSTEM + "\n\n输出格式要求：\n{format_instructions}"),
    ("user", "诊断：{diagnosis}\n症状：{symptoms}\n患者信息：{patient_info}\n相关参考资料：\n{context}"),
]).partial(format_instructions=_parser.get_format_instructions())


def recommend(
    diagnosis: str,
    symptoms: str,
    patient_info: dict | None,
    context: str,
) -> dict:
    parts = []
    if patient_info:
        parts.append(f"年龄={patient_info.get('age', '未知')}, 性别={patient_info.get('gender', '未知')}")
        if patient_info.get("medical_history"):
            parts.append(f"既往病史：{patient_info['medical_history']}")
        if patient_info.get("current_medications"):
            parts.append(f"当前用药：{patient_info['current_medications']}")
    info_text = "；".join(parts) if parts else "未提供"

    llm = get_llm(temperature=0.3)
    chain = TREATMENT_PROMPT | llm | _parser

    try:
        result: TreatmentPlan = chain.invoke({
            "diagnosis": diagnosis,
            "symptoms": symptoms,
            "patient_info": info_text,
            "context": context or "无相关参考资料",
        })
        return result.model_dump()
    except Exception as e:
        logger.warning(f"Treatment recommendation failed: {e}")

    return TreatmentPlan(
        immediate_actions=["请咨询医疗专业人士进行适当评估。"],
        medications=[],
        lifestyle_recommendations=["保持健康饮食和充足水分摄入。"],
        follow_up="请预约您的初级保健医生进行进一步检查。",
        disclaimer="本内容为AI生成的医疗信息仅供参考，请务必咨询持牌医疗专业人士获取实际诊疗意见。",
    ).model_dump()
