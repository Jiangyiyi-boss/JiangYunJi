"""
Elasticsearch 搜索服务
"""
import re
import logging
from datetime import datetime
from typing import Optional
from elasticsearch import Elasticsearch
from config import settings
from .es_client import es_client

logger = logging.getLogger(__name__)

PRODUCT_INDEX = settings.ES_INDEX
COURSE_INDEX = settings.ES_COURSE_INDEX


# ES 高亮标签，用于前端之前清洗成纯文本
_HIGHLIGHT_RE = re.compile(r"<em>|</em>", re.IGNORECASE)


def _strip_highlight(text: str) -> str:
    """移除 ES 高亮标签，避免前端直接显示 <em> 文本"""
    if not text:
        return text
    return _HIGHLIGHT_RE.sub("", text)


class SearchService:
    """商品和课程搜索服务"""

    def __init__(self, es: Elasticsearch = None):
        self.es = es or es_client
        self.index = PRODUCT_INDEX

    def search(
        self,
        keyword: str = "",
        page: int = 1,
        size: int = 20,
        sort_by: str = "_score",
        sort_order: str = "desc",
        category: Optional[str] = None,
        search_after: Optional[list] = None,
    ) -> dict:
        """
        商品全文检索

        Args:
            keyword: 搜索关键词
            page: 页码
            size: 每页数量
            sort_by: 排序字段 (_score, price, sales, created_at)
            sort_order: 排序方向 (asc, desc)
            category: 分类名称（来自首页分类导航）
            search_after: 游标分页 token

        Returns:
            搜索结果字典
        """
        # 构建查询
        must_clauses = []
        filter_clauses = [{"term": {"status": "approved"}}]

        if keyword:
            must_clauses.append({
                "multi_match": {
                    "query": keyword,
                    "fields": ["name^3", "description"],
                    "type": "best_fields",
                    "operator": "and",
                }
            })

        if category:
            filter_clauses.append({"term": {"category": category}})

        # 构建排序
        sort = []
        if sort_by == "price":
            sort.append({"price": {"order": sort_order}})
        elif sort_by == "sales":
            sort.append({"sales": {"order": sort_order}})
        elif sort_by == "created_at":
            sort.append({"created_at": {"order": sort_order}})
        else:
            sort.append({"_score": {"order": "desc"}})

        # 执行搜索
        body = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses,
                }
            },
            "sort": sort,
            "size": size,
            "highlight": {
                "fields": {
                    "name": {"pre_tags": ["<em>"], "post_tags": ["</em>"]},
                    "description": {"pre_tags": ["<em>"], "post_tags": ["</em>"]},
                }
            },
        }

        if search_after:
            body["search_after"] = search_after
        else:
            body["from"] = (page - 1) * size

        try:
            start_time = datetime.now()
            response = self.es.search(index=self.index, body=body)
            took_ms = (datetime.now() - start_time).total_seconds() * 1000

            hits = response["hits"]
            total = hits["total"]["value"]
            results = []

            for hit in hits["hits"]:
                source = hit["_source"]
                highlight = hit.get("highlight", {})
                results.append({
                    "id": source.get("id"),
                    "name": _strip_highlight(highlight.get("name", [source.get("name", "")])[0]),
                    "description": _strip_highlight(highlight.get("description", [source.get("description", "")])[0]),
                    "price": source.get("price", 0),
                    "original_price": source.get("original_price"),
                    "images": source.get("images", []),
                    "sales": source.get("sales", 0),
                    "stock": source.get("stock", 0),
                    "category": source.get("category", ""),
                    "brand": source.get("brand", ""),
                    "status": source.get("status", ""),
                    "score": hit.get("_score"),
                })

            has_more = False
            sa = None
            if hits["hits"]:
                last_hit = hits["hits"][-1]
                sa = last_hit.get("sort")
                has_more = len(results) >= size

            return {
                "results": results,
                "total": total,
                "page": page,
                "size": size,
                "has_more": has_more,
                "search_after": sa,
                "took_ms": round(took_ms, 2),
                "fallback": False,
            }
        except Exception as e:
            logger.error(f"ES 搜索失败: {e}")
            return {"error": str(e)}

    def search_courses(
        self,
        keyword: str = "",
        page: int = 1,
        size: int = 20,
        sort_by: str = "_score",
        sort_order: str = "desc",
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        is_free: Optional[bool] = None,
    ) -> dict:
        """
        课程全文检索

        Args:
            keyword: 搜索关键词
            page: 页码
            size: 每页数量
            sort_by: 排序字段 (_score, price, enrolled_count, created_at)
            sort_order: 排序方向 (asc, desc)
            category: 分类筛选
            difficulty: 难度筛选
            price_min: 最低价格
            price_max: 最高价格
            is_free: 是否免费

        Returns:
            搜索结果字典
        """
        # 构建查询
        must_clauses = []
        filter_clauses = [{"term": {"status": "published"}}]

        if keyword:
            must_clauses.append({
                "multi_match": {
                    "query": keyword,
                    "fields": ["title^3", "description", "craft_intro"],
                    "type": "best_fields",
                    "operator": "and",
                }
            })

        if category:
            filter_clauses.append({"term": {"category": category}})
        if difficulty:
            filter_clauses.append({"term": {"difficulty": difficulty}})
        if price_min is not None or price_max is not None:
            range_query = {}
            if price_min is not None:
                range_query["gte"] = price_min
            if price_max is not None:
                range_query["lte"] = price_max
            filter_clauses.append({"range": {"price": range_query}})
        if is_free is not None:
            filter_clauses.append({"term": {"is_free": is_free}})

        # 构建排序
        sort = []
        if sort_by == "price":
            sort.append({"price": {"order": sort_order}})
        elif sort_by == "enrolled_count":
            sort.append({"enrolled_count": {"order": sort_order}})
        elif sort_by == "created_at":
            sort.append({"created_at": {"order": sort_order}})
        else:
            sort.append({"_score": {"order": "desc"}})

        # 执行搜索
        body = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses,
                }
            },
            "sort": sort,
            "size": size,
            "highlight": {
                "fields": {
                    "title": {"pre_tags": ["<em>"], "post_tags": ["</em>"]},
                    "description": {"pre_tags": ["<em>"], "post_tags": ["</em>"]},
                    "craft_intro": {"pre_tags": ["<em>"], "post_tags": ["</em>"]},
                }
            },
        }

        body["from"] = (page - 1) * size

        try:
            start_time = datetime.now()
            response = self.es.search(index=COURSE_INDEX, body=body)
            took_ms = (datetime.now() - start_time).total_seconds() * 1000

            hits = response["hits"]
            total = hits["total"]["value"]
            results = []

            for hit in hits["hits"]:
                source = hit["_source"]
                highlight = hit.get("highlight", {})
                results.append({
                    "id": source.get("id"),
                    "title": _strip_highlight(highlight.get("title", [source.get("title", "")])[0]),
                    "description": _strip_highlight(highlight.get("description", [source.get("description", "")])[0]),
                    "craft_intro": _strip_highlight(highlight.get("craft_intro", [source.get("craft_intro", "")])[0]),
                    "price": source.get("price", 0),
                    "category": source.get("category", ""),
                    "difficulty": source.get("difficulty", ""),
                    "tags": source.get("tags", []),
                    "artisan_id": source.get("artisan_id"),
                    "artisan_name": source.get("artisan_name", ""),
                    "enrolled_count": source.get("enrolled_count", 0),
                    "lesson_count": source.get("lesson_count", 0),
                    "is_free": source.get("is_free", False),
                    "cover_image": source.get("cover_image", ""),
                    "status": source.get("status", ""),
                    "score": hit.get("_score"),
                })

            return {
                "results": results,
                "total": total,
                "page": page,
                "size": size,
                "has_more": (page * size) < total,
                "took_ms": round(took_ms, 2),
                "fallback": False,
            }
        except Exception as e:
            logger.error(f"ES 课程搜索失败: {e}")
            return {"error": str(e)}

    def suggest(self, prefix: str, size: int = 10) -> list:
        """搜索建议（自动补全）—— 与课程搜索 suggest_courses 完全一致的策略

        使用 match 查询 name 字段，IK 分词匹配。
        """
        suggestions = []
        seen = set()

        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "name": prefix
                                }
                            }
                        ],
                        "filter": [{"term": {"status": "approved"}}],
                    }
                },
                "size": size,
                "_source": ["name"],
            }
            response = self.es.search(index=self.index, body=search_body)
            for hit in response["hits"]["hits"]:
                name = hit["_source"]["name"]
                if name and name not in seen:
                    suggestions.append(name)
                    seen.add(name)
                if len(suggestions) >= size:
                    break
        except Exception as e:
            logger.error(f"ES 搜索建议失败: {e}")

        return suggestions[:size]

    def suggest_courses(self, prefix: str, size: int = 10) -> list:
        """课程搜索建议（自动补全）

        使用 multi_match 搜索课程标题和描述，返回匹配的课程标题列表。
        课程索引没有 completion 子字段，因此仅使用 multi_match 策略。
        """
        suggestions = []
        seen = set()

        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": prefix,
                                    "fields": ["title^3", "description"],
                                    "type": "best_fields",
                                }
                            }
                        ],
                        "filter": [{"term": {"status": "published"}}],
                    }
                },
                "size": size,
                "_source": ["title"],
            }
            response = self.es.search(index=COURSE_INDEX, body=search_body)
            for hit in response["hits"]["hits"]:
                title = hit["_source"]["title"]
                if title not in seen:
                    suggestions.append(title)
                    seen.add(title)
                if len(suggestions) >= size:
                    break
        except Exception as e:
            logger.error(f"课程搜索建议失败: {e}")

        return suggestions[:size]

    def log_search(self, keyword: str, total_results: int, took_ms: float):
        """记录搜索日志（可用于分析热门搜索）"""
        logger.info(f"搜索: '{keyword}', 结果: {total_results}, 耗时: {took_ms}ms")
