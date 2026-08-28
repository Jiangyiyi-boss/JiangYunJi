"""内存版会话记忆 — 单进程内按会话 ID 保存最近几轮问答。

特性:
- 无持久化: 后端进程重启即清空, 天然不留隐私
- 按会话隔离: 前端「新对话」生成新会话 ID, 即开启全新上下文
- 内存有上限: 单会话最多保留 MAX_MESSAGES 条(超出丢弃最早的),
  全局最多 MAX_SESSIONS 个会话(最久未使用优先淘汰)
- 线程安全: threading.Lock 保护, 可安全用于 FastAPI 并发请求
"""
import threading
from collections import OrderedDict

# 单会话最多保留 20 条消息(即 10 轮问答), 超出丢弃最早的消息
MAX_MESSAGES = 20

# 全局最多保留 1000 个会话, 超出后按 LRU 淘汰最久未使用的
MAX_SESSIONS = 1000


class InMemoryChatMemory:
    def __init__(self):
        # OrderedDict: key=session_id, value=[{role, content}, ...]
        # 顺序即访问顺序, 用于 LRU 淘汰
        self._sessions: "OrderedDict[str, list]" = OrderedDict()
        self._lock = threading.Lock()

    def get_history(self, session_id: str) -> list:
        """返回该会话的历史消息(不含当前问题), 无则返回空列表。"""
        with self._lock:
            return list(self._sessions.get(session_id, []))

    def save_exchange(self, session_id: str, question: str, answer: str) -> None:
        """保存一轮问答(user + assistant), 并做容量控制。"""
        if not session_id or not answer:
            return
        with self._lock:
            messages = self._sessions.setdefault(session_id, [])
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})
            # 只保留最近 MAX_MESSAGES 条
            if len(messages) > MAX_MESSAGES:
                del messages[: len(messages) - MAX_MESSAGES]
            # LRU: 最近使用的会话移到末尾
            self._sessions.move_to_end(session_id)
            # 会话数超限, 淘汰最久未使用的
            while len(self._sessions) > MAX_SESSIONS:
                self._sessions.popitem(last=False)

    def clear(self, session_id: str) -> None:
        """删除指定会话的记忆。"""
        with self._lock:
            self._sessions.pop(session_id, None)

    def clear_all(self) -> None:
        """清空全部会话(调试用)。"""
        with self._lock:
            self._sessions.clear()

    def stats(self) -> dict:
        """当前会话数与总消息数(调试用)。"""
        with self._lock:
            return {
                "sessions": len(self._sessions),
                "messages": sum(len(v) for v in self._sessions.values()),
            }


# 全局单例, 供 router 使用
chat_memory = InMemoryChatMemory()
