import logging
from langchain_core.prompts import ChatPromptTemplate
from agents.base import get_llm, get_parser
from models import TriageResult

logger = logging.getLogger(__name__)

_parser = get_parser(TriageResult)

TRIAGE_SYSTEM = """你是一名医疗分诊专家AI助手。你的职责是评估患者症状并判断紧急程度。

请分析患者的症状，提供以下结构化分诊评估：
1. 紧急程度: low(可自我护理), medium(数日内就医), high(当日就医), emergency(立即去急诊)
2. 建议的即时行动
3. 建议的就诊科室（如适用）

重要提示：这仅是AI初步评估，请务必告知患者需要寻求专业医疗帮助。"""

TRIAGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TRIAGE_SYSTEM + "\n\n输出格式要求：\n{format_instructions}"),
    ("user", "患者症状：{symptoms}\n持续时间：{duration}\n自述严重程度：{severity}"),
]).partial(format_instructions=_parser.get_format_instructions())


def triage(symptoms: str, duration: str = "", severity: str = "") -> dict:
    llm = get_llm(temperature=0.3)
    chain = TRIAGE_PROMPT | llm | _parser

    try:
        result: TriageResult = chain.invoke({
            "symptoms": symptoms,
            "duration": duration or "未提供",
            "severity": severity or "未提供",
        })
        return result.model_dump()
    except Exception as e:
        logger.warning(f"Triage failed: {e}")

    return TriageResult(
        urgency="medium",
        recommended_action="请咨询医疗专业人士进行适当评估。",
        specialty=None,
    ).model_dump()
