import logging
from agents.base import llm_chat

logger = logging.getLogger(__name__)

VALID_URGENCIES = {"low", "medium", "high", "emergency"}

TRIAGE_PROMPT = """你是一名医疗分诊专家AI助手。你的职责是评估患者症状并判断紧急程度。

请分析患者的症状，提供以下结构化分诊评估：
1. 紧急程度: low(可自我护理), medium(数日内就医), high(当日就医), emergency(立即去急诊)
2. 建议的即时行动
3. 建议的就诊科室（如适用）

重要提示：这仅是AI初步评估，请务必告知患者需要寻求专业医疗帮助。

请以JSON格式回复，urgency字段必须用英文值(low/medium/high/emergency)，其余字段用中文描述：
{
  "urgency": "medium",
  "recommended_action": "具体的行动建议",
  "specialty": "建议科室"
}"""


def triage(symptoms: str, duration: str = "", severity: str = "") -> dict:
    user_msg = f"患者症状：{symptoms}"
    if duration:
        user_msg += f"\n持续时间：{duration}"
    if severity:
        user_msg += f"\n自述严重程度：{severity}"

    try:
        result = llm_chat(TRIAGE_PROMPT, user_msg)
        import json
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(result[start:end])
            urgency = str(data.get("urgency", "")).strip().lower()
            if urgency not in VALID_URGENCIES:
                urgency = "medium"
            return {
                "urgency": urgency,
                "recommended_action": str(data.get("recommended_action", "请咨询医疗专业人士进行评估。")),
                "specialty": data.get("specialty") if data.get("specialty") else None,
            }
    except Exception as e:
        logger.warning(f"Triage JSON parse failed: {e}")

    return {
        "urgency": "medium",
        "recommended_action": "请咨询医疗专业人士进行适当评估。",
        "specialty": None,
    }
