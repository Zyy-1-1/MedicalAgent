"""
症状分析智能体 — AutoGen AssistantAgent

使用 AutoGen 智能体系统性分析患者症状，提取关键症状、列出可能疾病，
并标记紧急情况。
"""
import logging
from autogen import AssistantAgent
from agents.base import get_autogen_llm_config, run_agent, parse_json_response
from models import SymptomAnalysis

logger = logging.getLogger(__name__)

_DEFAULT = SymptomAnalysis(
    key_symptoms=[],
    possible_conditions=["信息不足，无法确定"],
    requires_emergency=False,
)

ANALYSIS_SYSTEM = """你是一名医疗症状分析AI助手。你的职责是系统性地分析患者报告的症状。

请分析给定症状并输出 JSON，包含以下字段：
- key_symptoms: 从描述中提取的关键症状列表（字符串数组，使用中文）
- possible_conditions: 可能解释这些症状的疾病列表（使用中文）
- requires_emergency: 布尔值，是否存在提示医疗紧急情况的症状（中风、心脏病、过敏性休克等）

只输出 JSON，不要在 JSON 前后添加任何其他内容。"""

analysis_agent = AssistantAgent(
    name="SymptomAnalyst",
    system_message=ANALYSIS_SYSTEM,
    llm_config=get_autogen_llm_config(temperature=0.3),
)


async def analyze(symptoms: str, duration: str = "", severity: str = "") -> dict:
    """使用 AutoGen 症状分析智能体进行分析。

    Args:
        symptoms: 症状描述
        duration: 持续时长
        severity: 严重程度

    Returns:
        SymptomAnalysis 的 model_dump() 字典
    """
    message = (
        f"请分析以下症状：{symptoms}\n"
        f"持续时间：{duration or '未提供'}\n"
        f"严重程度：{severity or '未提供'}"
    )

    try:
        reply = await run_agent(analysis_agent, message)
        logger.debug(f"Analysis agent reply: {reply[:200]}...")
        return parse_json_response(reply, SymptomAnalysis, lambda: _DEFAULT)
    except Exception as e:
        logger.warning(f"Symptom analysis agent failed: {e}")
        return _DEFAULT.model_dump()
