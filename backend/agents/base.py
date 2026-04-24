import logging
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def get_llm_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=60.0,
            max_retries=2,
        )
    return _client


def llm_chat(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            timeout=60.0,
        )
        content = response.choices[0].message.content
        return content or ""
    except (APIError, APIConnectionError, APITimeoutError) as e:
        logger.error(f"LLM API error: {e}")
        return "{}"
    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}")
        return "{}"


def llm_chat_with_history(
    system_prompt: str,
    history: list[dict],
    user_message: str,
    temperature: float = 0.3,
) -> str:
    try:
        client = get_llm_client()
        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=temperature,
            timeout=60.0,
        )
        content = response.choices[0].message.content
        return content or "抱歉，我暂时无法回复，请稍后再试。"
    except (APIError, APIConnectionError, APITimeoutError) as e:
        logger.error(f"LLM API error in chat: {e}")
        return "抱歉，API 服务暂时不可用，请稍后重试。"
    except Exception as e:
        logger.error(f"Unexpected LLM error in chat: {e}")
        return "抱歉，发生了未知错误，请重试。"
