"""LangGraph 文案工作流图构建"""
from langgraph.graph import StateGraph, START, END

from ai.copywriting.state import ContentState
from ai.copywriting.nodes import (
    classify_mode,
    generate_copy,
    polish_copy,
    merge_copy,
    generate_skill_intro,
)


def route_by_mode(state: ContentState) -> str:
    """条件边: 根据 mode 路由到生成或润色节点"""
    if state.get("mode") == "generate":
        return "generate_copy"
    return "polish_copy"


def build_graph() -> StateGraph:
    """构建文案生成/润色 LangGraph 工作流"""

    workflow = StateGraph(ContentState)

    # ── 添加节点 ──
    workflow.add_node("classify_mode", classify_mode)
    workflow.add_node("generate_copy", generate_copy)
    workflow.add_node("polish_copy", polish_copy)
    workflow.add_node("merge_copy", merge_copy)
    workflow.add_node("generate_skill_intro", generate_skill_intro)

    # ── 添加边 ──

    # 入口 → 分类
    workflow.add_edge(START, "classify_mode")

    # 分类 → 条件分支
    workflow.add_conditional_edges(
        "classify_mode",
        route_by_mode,
        {
            "generate_copy": "generate_copy",
            "polish_copy": "polish_copy",
        },
    )

    # 两条分支 → 合并
    workflow.add_edge("generate_copy", "merge_copy")
    workflow.add_edge("polish_copy", "merge_copy")

    # 合并 → 技艺介绍 → 结束
    workflow.add_edge("merge_copy", "generate_skill_intro")
    workflow.add_edge("generate_skill_intro", END)

    return workflow.compile()
