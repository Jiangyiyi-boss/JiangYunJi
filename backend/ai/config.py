"""AI 模块公共配置 - DeepSeek LLM 客户端"""
from langchain_openai import ChatOpenAI
from config import settings


def get_llm() -> ChatOpenAI:
    """获取 DeepSeek LLM 实例 (OpenAI 兼容协议)"""
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0.7,
        max_tokens=2048,
        timeout=settings.AI_TIMEOUT,
    )
