"""非遗百晓生聊天链 - 流式输出（内存版会话记忆, 支持会话内多轮追问）"""
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai.config import get_llm
from ai.chat.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def chat_stream(query: str, history: list | None = None):
    """
    会话内多轮流式问答: 逐 token 输出, 供 SSE 转发。

    history: 该会话之前若干轮的消息列表, 形如
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        由 router 从内存记忆(ai.chat.memory)读取, 传 None/[] 则为单轮独立问答。
    返回 async generator, yield 每个 token 字符串。
    """
    llm = get_llm()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if history:
        for item in history:
            content = item.get("content", "")
            if item.get("role") == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=query))

    full_response = ""
    try:
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_response += token
                yield token
    except Exception as e:
        logger.error("chat_stream error: %s", e)
        yield f"[ERROR] AI 响应失败: {e}"
        return

    logger.info(
        "chat_stream done: query_len=%s, response_len=%s, history_rounds=%s",
        len(query), len(full_response), len(history) // 2 if history else 0,
    )
