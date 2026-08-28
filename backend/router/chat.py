"""
AI 非遗知识问答路由
使用 LangChain ChatOpenAI 实现，SSE 流式输出, 前端逐字渲染, 实现打字机效果。

会话记忆：内存版（ai.chat.memory），按「用户ID:会话ID」隔离。
- 前端「新对话」生成新会话 ID → 全新上下文
- 刷新页面 / 后端重启 → 记忆自然清空，不落任何持久化存储
"""
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from dependencies import get_current_user
from models import User
from ai.chat.chain import chat_stream
from ai.chat.memory import chat_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    # 会话 ID: 前端每次「新对话」生成新 ID; 为空则视为一次性单轮问答(不保存记忆)
    conversation_id: str = Field(default="", description="会话ID, 空表示单轮问答")


@router.post("/messages")
async def chat_messages(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    发送消息到非遗百晓生 AI, 返回 SSE 流式响应。
    前端逐字渲染, 实现打字机效果。

    带 conversation_id 时: 注入该会话内存历史 → 多轮上下文, 结束后保存本轮
    不带 conversation_id 时: 单轮独立问答, 不读不写记忆
    """
    logger.info(
        "Chat request: user=%s, query_len=%s, conversation_id=%s",
        current_user.id, len(req.query), bool(req.conversation_id),
    )

    # 会话 key 绑定用户, 防止不同用户串记忆
    session_key = f"{current_user.id}:{req.conversation_id}" if req.conversation_id else ""
    history = chat_memory.get_history(session_key) if session_key else []

    async def event_stream():
        full_answer = ""
        try:
            async for token in chat_stream(req.query, history):
                full_answer += token
                # 每个 token 作为 SSE message 事件发送
                yield f"data: {json.dumps({'event': 'message', 'answer': token})}\n\n"

            # 发送 message_end 事件
            yield f"data: {json.dumps({'event': 'message_end', 'metadata': {}})}\n\n"

            # 流正常结束且非错误响应时, 保存本轮对话到内存记忆
            if session_key and full_answer and not full_answer.startswith("[ERROR]"):
                chat_memory.save_exchange(session_key, req.query, full_answer)

        except Exception as e:
            logger.error("Chat stream error: %s", e)
            yield f"data: {json.dumps({'event': 'error', 'message': '服务异常，请稍后重试'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
