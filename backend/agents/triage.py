"""
分诊智能体 — AutoGen AssistantAgent

使用 AutoGen 智能体评估患者症状的紧急程度，输出结构化分诊结果。
"""
import logging
from autogen import AssistantAgent
from agents.base import get_autogen_llm_config, run_agent, parse_json_response
from models import TriageResult

logger = logging.getLogger(__name__)

_DEFAULT = TriageResult(
    urgency="medium",
    recommended_action="请咨询医疗专业人士进行适当评估。",
    specialty=None,
)

TRIAGE_SYSTEM = """你是一名医疗分诊专家AI助手。你的职责是评估患者症状并判断紧急程度。

请分析患者的症状，输出 JSON 格式的分诊评估，包含以下字段：
- urgency: 紧急程度，只能是以下之一：
  - "low" — 可自我护理，无需急于就医
  - "medium" — 建议数日内就医
  - "high" — 建议当日就医
  - "emergency" — 立即去急诊
- recommended_action: 建议的即时行动（中文）
- specialty: 建议的就诊科室（如内科、外科、神经内科等），如果不确定则设为 null

重要提示：这仅是AI初步评估，请务必告知患者需要寻求专业医疗帮助。
只输出 JSON，不要在 JSON 前后添加任何其他内容。"""

triage_agent = AssistantAgent(
    name="TriageAgent",
    system_message=TRIAGE_SYSTEM,
    llm_config=get_autogen_llm_config(temperature=0.3),
)


async def triage(symptoms: str, duration: str = "", severity: str = "") -> dict:
    """使用 AutoGen 分诊智能体进行评估。

    Args:
        symptoms: 患者症状描述
        duration: 持续时长
        severity: 自述严重程度

    Returns:
        TriageResult 的 model_dump() 字典
    """
    message = (
        f"患者症状：{symptoms}\n"
        f"持续时间：{duration or '未提供'}\n"
        f"自述严重程度：{severity or '未提供'}"
    )

    try:
        reply = await run_agent(triage_agent, message)
        logger.debug(f"Triage agent reply: {reply[:200]}...")
        return parse_json_response(reply, TriageResult, lambda: _DEFAULT)
    except Exception as e:
        logger.warning(f"Triage agent failed: {e}")
        return _DEFAULT.model_dump()
