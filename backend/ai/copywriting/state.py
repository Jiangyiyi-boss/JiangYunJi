"""LangGraph 状态定义"""
from typing import Literal, Optional
from typing_extensions import TypedDict


class ContentState(TypedDict):
    """文案生成/润色工作流状态"""

    # ── 输入字段 ──
    content_type: Literal["product_description", "course_intro"]
    title: str
    user_input: str

    # ── 分类结果 ──
    mode: Literal["generate", "polish"]   # ≤20字→generate, >20字→polish
    length: int

    # ── 分支结果 ──
    generated_text: str                    # generate_copy 输出
    polished_text: str                     # polish_copy 输出

    # ── 合并后 ──
    final_text: str                        # merge_copy 输出

    # ── 最终输出 ──
    skill_intro: str                       # generate_skill_intro 输出 (商品时为空串)

    # ── 错误 ──
    error: Optional[str]
