"""
敏感词过滤模块
"""


class SensitiveFilter:
    """敏感词过滤器"""

    def __init__(self):
        # 敏感词列表（可根据需要扩展）
        self.words = [
            "敏感词1",
            "敏感词2",
        ]

    def check(self, text: str) -> tuple:
        """
        检查文本是否包含敏感词

        Returns:
            (is_safe, matched_words): is_safe为True表示安全，matched_words为匹配到的敏感词列表
        """
        if not text:
            return True, []

        matched = [w for w in self.words if w in text]
        return len(matched) == 0, matched


sensitive_filter = SensitiveFilter()
