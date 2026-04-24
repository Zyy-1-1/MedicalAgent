import logging
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from config import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """返回 LangChain ChatOpenAI 实例。"""
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=temperature,
        timeout=60.0,
        max_retries=2,
    )


def get_parser(pydantic_model: type) -> PydanticOutputParser:
    """返回 PydanticOutputParser，用于从 LLM 文本输出中解析结构化 JSON。"""
    return PydanticOutputParser(pydantic_object=pydantic_model)
