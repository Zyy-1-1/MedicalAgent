import json
import logging
from agents.base import llm_chat

logger = logging.getLogger(__name__)

SYMPTOM_ANALYZER_PROMPT = """你是一名医疗症状分析AI助手。你的职责是系统性地分析报告的症状。

请分析给定症状并完成：
1. 从描述中识别关键症状
2. 列出可能解释这些症状的疾病（鉴别列表）
3. 标记是否存在提示医疗紧急情况的症状（中风、心脏病、过敏性休克等）

请以JSON格式回复，用中文描述：
{
  "key_symptoms": ["症状1", "症状2"],
  "possible_conditions": ["可能疾病1", "可能疾病2"],
  "requires_emergency": false
}"""


def analyze(symptoms: str, duration: str = "", severity: str = "") -> dict:
    user_msg = f"请分析以下症状：{symptoms}"
    if duration:
        user_msg += f"\n持续时间：{duration}"
    if severity:
        user_msg += f"\n严重程度：{severity}"

    try:
        result = llm_chat(SYMPTOM_ANALYZER_PROMPT, user_msg)
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(result[start:end])
            return {
                "key_symptoms": data.get("key_symptoms", [symptoms[:50]]) if isinstance(data.get("key_symptoms"), list) else [str(data.get("key_symptoms", symptoms[:50]))],
                "possible_conditions": data.get("possible_conditions", []) if isinstance(data.get("possible_conditions"), list) else [],
                "requires_emergency": bool(data.get("requires_emergency", False)),
            }
    except Exception as e:
        logger.warning(f"Symptom analysis JSON parse failed: {e}")

    return {
        "key_symptoms": [symptoms[:50]],
        "possible_conditions": ["信息不足，无法确定"],
        "requires_emergency": False,
    }
