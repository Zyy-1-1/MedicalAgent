import json
import logging
from agents.base import llm_chat

logger = logging.getLogger(__name__)

TREATMENT_PROMPT = """你是一名医疗治疗建议AI助手。基于诊断结果，提供治疗计划建议。

根据诊断和患者情况，提供：
1. 患者应立即采取的措施
2. 可能的用药方案（仅通用药名；不要指定具体剂量）
3. 生活方式建议
4. 随访建议

重要：务必声明此为AI生成信息，不是医疗建议。不要处方管制类药物。建议患者在服用任何药物前咨询医生。

请以JSON格式回复，用中文描述：
{
  "immediate_actions": ["措施1", "措施2"],
  "medications": ["常用药物1", "常用药物2"],
  "lifestyle_recommendations": ["建议1", "建议2"],
  "follow_up": "随访计划描述",
  "disclaimer": "免责声明"
}"""


def recommend(
    diagnosis: str,
    symptoms: str,
    patient_info: dict | None,
    context: str,
) -> dict:
    user_msg = f"诊断：{diagnosis}\n症状：{symptoms}\n"

    if patient_info:
        user_msg += f"患者：年龄={patient_info.get('age', '未知')}, "
        user_msg += f"性别={patient_info.get('gender', '未知')}\n"
        if patient_info.get("medical_history"):
            user_msg += f"既往病史：{patient_info['medical_history']}\n"

    if context:
        user_msg += f"\n相关参考资料：\n{context}"

    try:
        result = llm_chat(TREATMENT_PROMPT, user_msg)
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(result[start:end])
            def _to_list(val, default):
                if isinstance(val, list):
                    return val
                if isinstance(val, str):
                    return [val]
                return default
            return {
                "immediate_actions": _to_list(data.get("immediate_actions"), ["请咨询医疗专业人士进行适当评估。"]),
                "medications": _to_list(data.get("medications"), []),
                "lifestyle_recommendations": _to_list(data.get("lifestyle_recommendations"), ["保持健康饮食和充足水分摄入。"]),
                "follow_up": str(data.get("follow_up", "请预约您的初级保健医生进行进一步检查。")),
                "disclaimer": str(data.get("disclaimer", "本内容为AI生成的医疗信息仅供参考，请务必咨询持牌医疗专业人士获取实际诊疗意见。")),
            }
    except Exception as e:
        logger.warning(f"Treatment JSON parse failed: {e}")

    return {
        "immediate_actions": ["请咨询医疗专业人士进行适当评估。"],
        "medications": [],
        "lifestyle_recommendations": ["保持健康饮食和充足水分摄入。"],
        "follow_up": "请预约您的初级保健医生进行进一步检查。",
        "disclaimer": "本内容为AI生成的医疗信息仅供参考，请务必咨询持牌医疗专业人士获取实际诊疗意见。",
    }
