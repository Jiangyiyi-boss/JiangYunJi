"""文案生成/润色/技艺介绍三个 Prompt 模板"""
from langchain_core.prompts import ChatPromptTemplate

# ── 生成文案 Prompt ──
GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的非遗电商文案策划师。请根据以下信息生成文案：

文案类型：{content_type}
- 如果是 product_description：生成商品详细描述（不超过200字）
- 如果是 course_intro：生成课程简介（不超过500字）

商品/课程名称：{title}
用户关键词：{user_input}

要求：
1. 突出非遗文化价值和匠人精神
2. 语言优美、通俗易懂、有吸引力
3. 符合电商平台文案风格
4. 严格控制字数限制
5. 直接输出文案内容，不要添加任何解释"""),
    ("human", "请根据以上要求生成文案。"),
])

# ── 润色文案 Prompt ──
POLISH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的非遗电商文案策划师。请对以下文案进行润色优化：

文案类型：{content_type}
- 如果是 product_description：商品详细描述（不超过200字）
- 如果是 course_intro：课程简介（不超过500字）

商品/课程名称：{title}
原始文案：{user_input}

润色要求：
1. 保留原文核心信息和意图
2. 优化语言表达，使其更流畅、更有吸引力
3. 突出非遗文化价值和匠人精神
4. 符合电商平台文案风格
5. 严格控制字数限制
6. 直接输出润色后的文案，不要添加任何解释"""),
    ("human", "请根据以上要求润色文案。"),
])

# ── 技艺介绍 Prompt ──
SKILL_INTRO_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一位专业的非遗电商文案策划师。

文案类型：{content_type}

如果文案类型是 product_description：
请直接输出空字符串，不要输出任何其他内容。

如果文案类型是 course_intro：
请根据以下课程简介生成技术介绍：

课程名称：{title}
课程简介：{final_text}

技术介绍要求：
1. 基于课程简介内容，提炼核心技术要点
2. 融入非遗文化底蕴和历史传承
3. 突出技艺的专业性和独特性
4. 不超过 500 字
5. 直接输出技术介绍内容，不要添加任何解释"""),
    ("human", "请根据以上要求生成输出。"),
])
