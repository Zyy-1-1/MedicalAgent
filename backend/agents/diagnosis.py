import json
import logging
from agents.base import llm_chat

logger = logging.getLogger(__name__)

VALID_CONFIDENCES = {"low", "moderate", "high"}

DIAGNOSIS_PROMPT = """你是一名医疗诊断AI助手。基于症状和医学知识，提供鉴别诊断。

根据患者症状、病史和相关医学参考资料，提供：
1. 最可能的初步诊断
2. 鉴别诊断列表（其他可能疾病）
3. 置信度: low(低)/moderate(中等)/high(高)
4. 临床推理过程

重要提示：你是AI助手而非医生。务必声明评估仅为初步判断，患者必须咨询医疗专业人士。不要做出确诊。

请以JSON格式回复，confidence字段必须用英文值(low/moderate/high)，其余用中文描述：
{
  "primary_diagnosis": "最可能的疾病",
  "differential_diagnoses": ["其他可能疾病1", "其他可能疾病2"],
  "confidence": "moderate",
  "reasoning": "临床推理过程"
}"""


def diagnose(symptoms: str, patient_info: dict | None, context: str) -> dict:
    user_msg = f"患者症状：{symptoms}\n"

    if patient_info:
        user_msg += f"患者信息：年龄={patient_info.get('age', '未知')}, "
        user_msg += f"性别={patient_info.get('gender', '未知')}\n"
        if patient_info.get("medical_history"):
            user_msg += f"既往病史：{patient_info['medical_history']}\n"
        if patient_info.get("current_medications"):
            user_msg += f"当前用药：{patient_info['current_medications']}\n"

    if context:
        user_msg += f"\n相关医学参考资料：\n{context}"

    try:
        result = llm_chat(DIAGNOSIS_PROMPT, user_msg)
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(result[start:end])
            confidence = str(data.get("confidence", "moderate")).strip().lower()
            if confidence not in VALID_CONFIDENCES:
                confidence = "moderate"
            return {
                "primary_diagnosis": str(data.get("primary_diagnosis", "信息不足，无法确定")),
                "differential_diagnoses": data.get("differential_diagnoses", []) if isinstance(data.get("differential_diagnoses"), list) else [],
                "confidence": confidence,
                "reasoning": str(data.get("reasoning", "由于信息不足，无法完成诊断分析。")),
            }
    except Exception as e:
        logger.warning(f"Diagnosis JSON parse failed: {e}")

    return {
        "primary_diagnosis": "信息不足，无法确定",
        "differential_diagnoses": [],
        "confidence": "low",
        "reasoning": "由于信息不足，无法完成诊断分析。",
    }
