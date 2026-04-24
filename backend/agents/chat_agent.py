import logging
from agents.base import llm_chat_with_history
from memory import get_history, add_message
from rag import retriever
from models import RetrievedDocument

logger = logging.getLogger(__name__)

CHAT_PROMPT = """你是一名乐于助人的医疗AI助手。你可以讨论症状、回答一般健康问题，并提供医疗信息。

准则：
- 你不是医生。请始终说明你提供的是信息而非医疗建议。
- 如果用户描述症状，必要时请追问以澄清细节。
- 保持回复清晰并富有同情心。
- 在相关时引用医学知识。
- 如果症状听起来属于紧急情况，强烈建议用户立即前往急诊。
- 不要处方药物或做确诊诊断。
- 使用中文回复。"""


async def handle_chat(session_id: str, message: str) -> str:
    add_message(session_id, "user", message)
    history = get_history(session_id)

    # Retrieve relevant medical knowledge
    retrieved = retriever.retrieve(message, top_k=2)
    context = ""
    if retrieved:
        context = "[相关医学知识参考]\n"
        for doc in retrieved:
            context += f"- {doc['content']}\n"

    system_with_context = CHAT_PROMPT
    if context:
        system_with_context += f"\n\n{context}"

    reply = llm_chat_with_history(system_with_context, history, message, temperature=0.5)
    add_message(session_id, "assistant", reply)
    return reply
