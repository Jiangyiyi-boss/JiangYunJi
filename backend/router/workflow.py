"""
AI 文案生成路由
使用 LangGraph 工作流替代 Dify Workflow API

工作流流程:
  开始 → classify_mode(判断输入长度) → 条件分支
    ├─ IF (mode=="generate", ≤20字): generate_copy (LLM 生成文案)
    └─ ELSE (mode=="polish", >20字):  polish_copy (LLM 润色文案)
  → merge_copy(合并分支结果) → generate_skill_intro(技艺介绍)
  → 输出: result(文案), tech_intro(技艺介绍)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from dependencies import require_role
from models import User
from ai.copywriting.graph import build_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# ── 工作流实例 (编译一次, 重复使用) ──
_copywriting_graph = None


def get_copywriting_graph():
    """懒加载编译好的 LangGraph 工作流"""
    global _copywriting_graph
    if _copywriting_graph is None:
        _copywriting_graph = build_graph()
    return _copywriting_graph


# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------

class GenerateCopyRequest(BaseModel):
    """文案生成请求参数"""
    content_type: Literal["product_description", "course_intro"] = Field(
        ...,
        description="文案类型: product_description=商品描述, course_intro=课程简介",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="商品名称或课程标题",
    )
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="商家输入的文案内容(≤20字走生成分支, >20字走润色分支)",
    )


class GenerateCopyResponse(BaseModel):
    result: str = Field(default="", description="生成/润色后的文案")
    tech_intro: str = Field(default="", description="技艺介绍(仅 course_intro 有值)")


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateCopyResponse)
async def generate_copy(
    req: GenerateCopyRequest,
    current_user: User = Depends(require_role("artisan")),
):
    """
    调用 LangGraph 工作流生成/润色文案。

    仅匠人角色可用。

    工作流内部逻辑:
    - user_input ≤ 20 字符 → 走"文案生成"分支
    - user_input > 20 字符 → 走"文案润色"分支
    - content_type=product_description → 仅返回 result, tech_intro 为空
    - content_type=course_intro → 返回 result + tech_intro(技艺介绍)
    """
    graph = get_copywriting_graph()

    logger.info(
        "Workflow request: user=%s, content_type=%s, title=%s, input_len=%s",
        current_user.id, req.content_type, req.title, len(req.user_input),
    )

    try:
        result_state = await graph.ainvoke({
            "content_type": req.content_type,
            "title": req.title,
            "user_input": req.user_input,
        })
    except Exception as e:
        logger.error("LangGraph workflow error: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"AI 文案生成失败: {e}",
        )

    # 检查错误
    if result_state.get("error"):
        logger.error("Workflow returned error: %s", result_state["error"])
        raise HTTPException(
            status_code=500,
            detail=result_state["error"],
        )

    final_text = result_state.get("final_text", "")
    tech_intro = result_state.get("skill_intro", "")

    # 商品描述不需要技艺介绍, 确保清空
    if req.content_type == "product_description":
        tech_intro = ""

    if not final_text:
        logger.warning("Workflow returned empty result")

    logger.info(
        "Workflow finished: result_len=%s, tech_intro_len=%s",
        len(final_text), len(tech_intro),
    )

    return GenerateCopyResponse(
        result=final_text.strip(),
        tech_intro=tech_intro.strip(),
    )
