"""LangGraph 文案工作流节点函数"""
import logging

from ai.config import get_llm
from ai.copywriting.state import ContentState
from ai.copywriting.prompts import GENERATE_PROMPT, POLISH_PROMPT, SKILL_INTRO_PROMPT

logger = logging.getLogger(__name__)


# ── 节点 1: classify_mode ── 判断生成/润色模式 ──

def classify_mode(state: ContentState) -> dict:
    """
    根据用户输入长度判断模式:
    ≤20 字 → generate (生成)
    >20 字 → polish (润色)
    """
    user_input = state["user_input"]
    length = len(user_input.strip())
    mode = "generate" if length <= 20 else "polish"

    logger.info("classify_mode: length=%s, mode=%s", length, mode)
    return {"mode": mode, "length": length}


# ── 节点 2: generate_copy ── LLM 生成文案 ──

async def generate_copy(state: ContentState) -> dict:
    """调用 DeepSeek 生成文案 (≤20字走此分支)"""
    llm = get_llm()

    chain = GENERATE_PROMPT | llm
    response = await chain.ainvoke({
        "content_type": state["content_type"],
        "title": state["title"],
        "user_input": state["user_input"],
    })

    generated = response.content.strip()
    logger.info("generate_copy: output_len=%s", len(generated))
    return {"generated_text": generated}


# ── 节点 3: polish_copy ── LLM 润色文案 ──

async def polish_copy(state: ContentState) -> dict:
    """调用 DeepSeek 润色文案 (>20字走此分支)"""
    llm = get_llm()

    chain = POLISH_PROMPT | llm
    response = await chain.ainvoke({
        "content_type": state["content_type"],
        "title": state["title"],
        "user_input": state["user_input"],
    })

    polished = response.content.strip()
    logger.info("polish_copy: output_len=%s", len(polished))
    return {"polished_text": polished}


# ── 节点 4: merge_copy ── 合并分支结果 ──

def merge_copy(state: ContentState) -> dict:
    """合并生成/润色分支: 哪个有值取哪个"""
    final = state.get("generated_text", "") or state.get("polished_text", "")
    logger.info("merge_copy: final_len=%s", len(final))
    return {"final_text": final}


# ── 节点 5: generate_skill_intro ── 生成技艺介绍 ──

async def generate_skill_intro(state: ContentState) -> dict:
    """
    商品描述 → 返回空串
    课程简介 → 调用 DeepSeek 生成技艺介绍
    """
    content_type = state["content_type"]

    if content_type == "product_description":
        logger.info("generate_skill_intro: product_description → empty")
        return {"skill_intro": ""}

    llm = get_llm()
    chain = SKILL_INTRO_PROMPT | llm
    response = await chain.ainvoke({
        "content_type": content_type,
        "title": state["title"],
        "final_text": state["final_text"],
    })

    intro = response.content.strip()
    logger.info("generate_skill_intro: course_intro → intro_len=%s", len(intro))
    return {"skill_intro": intro}
