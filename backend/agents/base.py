"""
基础工具：LLM 配置工厂、AutoGen 智能体执行器、LangChain 输出解析器
"""
import json
import logging
from typing import Optional
from autogen import AssistantAgent, ConversableAgent
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from config import settings

logger = logging.getLogger(__name__)

# ── 全局 UserProxy（用于发起智能体对话，静默模式，无人类输入） ──
_user_proxy = ConversableAgent(
    name="UserProxy",
    llm_config=False,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
)


def get_autogen_llm_config(temperature: float = 0.3) -> dict:
    """返回 AutoGen AssistantAgent 所需的 LLM 配置。"""
    return {
        "config_list": [
            {
                "api_type": "openai",
                "model": settings.LLM_MODEL,
                "api_key": settings.OPENAI_API_KEY,
                "base_url": settings.OPENAI_BASE_URL,
            }
        ],
        "temperature": temperature,
        "timeout": 60,
    }


async def run_agent(agent: AssistantAgent, message: str) -> str:
    """向 AutoGen 智能体发送单轮消息并获取回复。

    Args:
        agent: AutoGen AssistantAgent 实例
        message: 发送给智能体的用户消息

    Returns:
        智能体的回复文本（字符串）
    """
    try:
        result = await _user_proxy.a_initiate_chat(
            recipient=agent,
            message=message,
            max_turns=1,
        )
        # result.chat_history 结构:
        # [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
        return result.chat_history[-1]["content"]
    except Exception as e:
        logger.error(f"AutoGen agent run failed: {e}")
        raise


def parse_json_response(reply: str, pydantic_model: type, default_factory) -> dict:
    """解析智能体的 JSON 回复为 Pydantic 模型字典。

    尝试顺序：
    1. 使用 LangChain PydanticOutputParser 解析
    2. 直接 json.loads + Pydantic 构造
    3. 使用默认工厂兜底

    Args:
        reply: 智能体的原始回复文本
        pydantic_model: Pydantic 模型类
        default_factory: 无参可调用对象，返回默认模型实例

    Returns:
        Pydantic 模型的 model_dump() 结果
    """
    # 尝试 1：LangChain 解析器
    try:
        parser = PydanticOutputParser(pydantic_object=pydantic_model)
        parsed = parser.parse(reply)
        return parsed.model_dump()
    except Exception as e1:
        logger.debug(f"LangChain parser failed: {e1}")

    # 尝试 2：手动 JSON 解析
    try:
        # 尝试提取 JSON 块（可能被 ```json ... ``` 包裹）
        text = reply.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        data = json.loads(text)
        return pydantic_model(**data).model_dump()
    except Exception as e2:
        logger.debug(f"Manual JSON parse failed: {e2}")

    # 兜底：默认值
    logger.warning(f"Falling back to default for {pydantic_model.__name__}")
    return default_factory().model_dump()


# ── 保留 LangChain ChatOpenAI 工厂（用于 chat_agent.py 等场景） ──

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
    """返回 LangChain PydanticOutputParser。"""
    return PydanticOutputParser(pydantic_object=pydantic_model)
