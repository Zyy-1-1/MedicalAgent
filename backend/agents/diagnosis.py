import logging
from langchain_core.prompts import ChatPromptTemplate
from agents.base import get_llm, get_parser
from models import DiagnosisResult

logger = logging.getLogger(__name__)

_parser = get_parser(DiagnosisResult)

DIAGNOSIS_SYSTEM = """你是一名医疗诊断AI助手。基于症状和医学知识，提供鉴别诊断。

根据患者症状、病史和相关医学参考资料，提供：
1. 最可能的初步诊断
2. 鉴别诊断列表（其他可能疾病）
3. 置信度: low(低)/moderate(中等)/high(高)
4. 临床推理过程

重要提示：你是AI助手而非医生。务必声明评估仅为初步判断，患者必须咨询医疗专业人士。不要做出确诊。"""

DIAGNOSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", DIAGNOSIS_SYSTEM + "\n\n输出格式要求：\n{format_instructions}"),
    ("user", "患者症状：{symptoms}\n患者信息：{patient_info}\n相关医学参考资料：\n{context}"),
]).partial(format_instructions=_parser.get_format_instructions())


def diagnose(symptoms: str, patient_info: dict | None, context: str) -> dict:
    parts = []
    if patient_info:
        parts.append(f"年龄={patient_info.get('age', '未知')}, 性别={patient_info.get('gender', '未知')}")
        if patient_info.get("medical_history"):
            parts.append(f"既往病史：{patient_info['medical_history']}")
        if patient_info.get("current_medications"):
            parts.append(f"当前用药：{patient_info['current_medications']}")
    info_text = "；".join(parts) if parts else "未提供"

    llm = get_llm(temperature=0.3)
    chain = DIAGNOSIS_PROMPT | llm | _parser

    try:
        result: DiagnosisResult = chain.invoke({
            "symptoms": symptoms,
            "patient_info": info_text,
            "context": context or "无相关参考资料",
        })
        return result.model_dump()
    except Exception as e:
        logger.warning(f"Diagnosis failed: {e}")

    return DiagnosisResult(
        primary_diagnosis="信息不足，无法确定",
        differential_diagnoses=[],
        confidence="low",
        reasoning="由于信息不足，无法完成诊断分析。",
    ).model_dump()
