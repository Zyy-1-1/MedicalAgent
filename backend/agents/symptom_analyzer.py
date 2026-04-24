import logging
from langchain_core.prompts import ChatPromptTemplate
from agents.base import get_llm, get_parser
from models import SymptomAnalysis

logger = logging.getLogger(__name__)

_parser = get_parser(SymptomAnalysis)

SYMPTOM_ANALYZER_SYSTEM = """你是一名医疗症状分析AI助手。你的职责是系统性地分析报告的症状。

请分析给定症状并完成：
1. 从描述中识别关键症状
2. 列出可能解释这些症状的疾病（鉴别列表）
3. 标记是否存在提示医疗紧急情况的症状（中风、心脏病、过敏性休克等）"""

SYMPTOM_ANALYZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYMPTOM_ANALYZER_SYSTEM + "\n\n输出格式要求：\n{format_instructions}"),
    ("user", "请分析以下症状：{symptoms}\n持续时间：{duration}\n严重程度：{severity}"),
]).partial(format_instructions=_parser.get_format_instructions())


def analyze(symptoms: str, duration: str = "", severity: str = "") -> dict:
    llm = get_llm(temperature=0.3)
    chain = SYMPTOM_ANALYZER_PROMPT | llm | _parser

    try:
        result: SymptomAnalysis = chain.invoke({
            "symptoms": symptoms,
            "duration": duration or "未提供",
            "severity": severity or "未提供",
        })
        return result.model_dump()
    except Exception as e:
        logger.warning(f"Symptom analysis failed: {e}")

    return SymptomAnalysis(
        key_symptoms=[symptoms[:50]],
        possible_conditions=["信息不足，无法确定"],
        requires_emergency=False,
    ).model_dump()
