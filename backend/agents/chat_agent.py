import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.base import get_llm
from memory import get_chat_history, add_message
from rag import retriever

logger = logging.getLogger(__name__)

CHAT_SYSTEM = """你是一名乐于助人的医疗AI助手。你可以讨论症状、回答一般健康问题，并提供医疗信息。

准则：
- 你不是医生。请始终说明你提供的是信息而非医疗建议。
- 如果用户描述症状，必要时请追问以澄清细节。
- 保持回复清晰并富有同情心。
- 在相关时引用医学知识。
- 如果症状听起来属于紧急情况，强烈建议用户立即前往急诊。
- 不要处方药物或做确诊诊断。
- 使用中文回复。"""

CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CHAT_SYSTEM),
    ("system", "{context}"),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}"),
])


async def handle_chat(session_id: str, message: str) -> str:
    add_message(session_id, "user", message)
    history = get_chat_history(session_id)

    # Retrieve relevant medical knowledge
    retrieved = retriever.retrieve(message, top_k=2)
    context = ""
    if retrieved:
        context = "[相关医学知识参考]\n"
        for doc in retrieved:
            context += f"- {doc['content']}\n"

    llm = get_llm(temperature=0.5)
    chain = CHAT_PROMPT | llm

    try:
        result = chain.invoke({
            "context": context,
            "history": history,
            "input": message,
        })
        reply = result.content
    except Exception as e:
        logger.error(f"Chat agent error: {e}")
        reply = "抱歉，发生了未知错误，请重试。"

    add_message(session_id, "assistant", reply)
    return reply
