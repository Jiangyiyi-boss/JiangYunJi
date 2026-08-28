"""
搜索 API 路由
包含：全文检索、搜索建议
"""
import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db
from es import SearchService
from es import (
    sync_product, delete_product_from_es, update_product_stock, update_product_sales, update_product_status,
    create_course_index, rebuild_course_index, sync_all_courses, delete_course_from_es,
)
from sensitive_words import sensitive_filter
from models import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["搜索"])


def get_search_service() -> SearchService:
    """获取搜索服务实例"""
    return SearchService()


# ==================== 全文检索 ====================

@router.get("/products")
async def search_products(
    keyword: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("_score", description="排序字段: _score, price, sales, created_at"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    category: Optional[str] = Query(None, description="分类名称（来自首页分类导航）"),
    search_after: Optional[str] = Query(None, description="游标分页 token (JSON 数组)"),
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """
    商品全文检索
    支持多字段检索、分类过滤、排序、分页（含 search_after 游标分页）
    """
    # 敏感词过滤
    if keyword:
        is_safe, matched = sensitive_filter.check(keyword)
        if not is_safe:
            return {
                "code": 400,
                "message": f"搜索词包含违规内容，请修改后重试",
                "data": None,
            }

    # 解析 search_after
    sa = None
    if search_after:
        import json
        try:
            sa = json.loads(search_after)
        except Exception:
            return {
                "code": 400,
                "message": "search_after 参数格式错误",
                "data": None,
            }

    # 执行搜索
    result = search_service.search(
        keyword=keyword,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
        category=category,
        search_after=sa,
    )

    # 异常降级处理
    if "error" in result:
        logger.warning(f"搜索降级: {result['error']}")
        # ES 不可用时，降级到 MySQL 搜索
        return _fallback_search(
            db, keyword, page, size, sort_by, sort_order, category
        )

    # ES 结果为空时，也尝试 MySQL 兜底（防止 ES 索引不同步或数据缺失）
    if result.get("total", 0) == 0 and (keyword or category):
        logger.info(f"ES 搜索结果为空，尝试 MySQL 兜底: keyword={keyword}, category={category}")
        fallback_result = _fallback_search(
            db, keyword, page, size, sort_by, sort_order, category
        )
        if fallback_result["data"]["total"] > 0:
            return fallback_result

    # 埋点记录
    search_service.log_search(
        keyword=keyword,
        total_results=result.get("total", 0),
        took_ms=result.get("took_ms", 0),
    )

    return {
        "code": 200,
        "message": "success",
        "data": result,
    }


def _fallback_search(
    db, keyword, page, size, sort_by, sort_order, category=None
):
    """ES 不可用或结果为空时的降级方案：MySQL 搜索"""
    query = db.query(Product).filter(Product.status == "approved")

    if keyword:
        query = query.filter(
            (Product.name.contains(keyword)) |
            (Product.description.contains(keyword))
        )

    if category:
        from models import Category
        cat = db.query(Category).filter(Category.name == category).first()
        if cat:
            descendant_ids = [cat.id]
            # 收集该分类下所有子分类
            def collect_descendants(parent_id, ids):
                children = db.query(Category).filter(Category.parent_id == parent_id).all()
                for child in children:
                    ids.append(child.id)
                    collect_descendants(child.id, ids)
            collect_descendants(cat.id, descendant_ids)
            query = query.filter(Product.category_id.in_(descendant_ids))

    # 排序：ES 的 _score 在 MySQL 中等价于 created_at desc
    if sort_by == "price":
        query = query.order_by(Product.price.asc() if sort_order == "asc" else Product.price.desc())
    elif sort_by == "sales":
        query = query.order_by(Product.sales.desc())
    elif sort_by == "created_at":
        query = query.order_by(Product.created_at.asc() if sort_order == "asc" else Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    total = query.count()
    products = query.offset((page - 1) * size).limit(size).all()

    results = []
    for p in products:
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "original_price": float(p.original_price) if p.original_price else None,
            "images": p.images or [],
            "sales": p.sales,
            "stock": p.stock,
            "category": p.category.name if p.category else "",
            "status": p.status,
        })

    return {
        "code": 200,
        "message": "success (降级模式)",
        "data": {
            "results": results,
            "total": total,
            "page": page,
            "size": size,
            "has_more": (page * size) < total,
            "search_after": None,
            "took_ms": 0,
            "fallback": True,
        },
    }


# ==================== 搜索建议 ====================

@router.get("/suggest")
async def search_suggest(
    prefix: str = Query(..., min_length=1, max_length=50, description="搜索前缀"),
    size: int = Query(10, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """搜索建议（自动补全）—— 与课程搜索完全一致的策略

    1. 先查 ES，有结果就直接返回
    2. ES 失败或无结果，降级到 MySQL LIKE 查询
    """
    # 敏感词过滤
    is_safe, matched = sensitive_filter.check(prefix)
    if not is_safe:
        return {
            "code": 400,
            "message": "搜索词包含违规内容",
            "data": [],
        }

    # 1. 尝试 ES 搜索建议
    try:
        suggestions = search_service.suggest(prefix, size)
        if suggestions:
            return {"code": 200, "message": "success", "data": suggestions}
    except Exception as e:
        logger.error(f"ES 搜索建议失败: {e}")

    # 2. 降级到 MySQL 查询
    items = db.query(Product).filter(
        Product.status == "approved",
        Product.name.contains(prefix),
    ).limit(size).all()
    suggestions = [p.name for p in items]
    return {"code": 200, "message": "success", "data": suggestions}

# ==================== 调试端点 ====================

@router.get("/debug/suggest")
async def debug_suggest(
    prefix: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """调试端点：分别查询 MySQL 和 ES，返回各自的原始结果

    用于排查搜索建议问题：访问
    http://<服务器IP>:8000/api/search/debug/suggest?prefix=花
    """
    # MySQL 查询
    mysql_results = []
    try:
        db_query = db.query(Product.id, Product.name, Product.status).filter(
            Product.name.like(f"%{prefix}%"),
        ).limit(20).all()
        for row in db_query:
            mysql_results.append({
                "id": row[0],
                "name": row[1],
                "status": row[2],
            })
    except Exception as e:
        mysql_results = [{"error": str(e)}]

    # 统计
    mysql_approved_count = sum(1 for r in mysql_results if isinstance(r, dict) and r.get("status") == "approved")

    # ES 查询
    es_results = []
    es_total = 0
    try:
        search_body = {
            "query": {
                "bool": {
                    "must": [{"match": {"name": prefix}}],
                    "filter": [{"term": {"status": "approved"}}],
                }
            },
            "size": 20,
            "_source": ["id", "name", "status"],
        }
        response = search_service.es.search(index=search_service.index, body=search_body)
        es_total = response["hits"]["total"]["value"]
        for hit in response["hits"]["hits"]:
            es_results.append({
                "id": hit["_source"].get("id"),
                "name": hit["_source"].get("name"),
                "status": hit["_source"].get("status"),
                "_score": hit.get("_score"),
            })
    except Exception as e:
        es_results = [{"error": str(e)}]

    return {
        "code": 200,
        "prefix": prefix,
        "mysql": {
            "total_with_keyword": len(mysql_results),
            "approved_count": mysql_approved_count,
            "results": mysql_results,
        },
        "es": {
            "total": es_total,
            "results": es_results,
        },
    }


# ==================== 索引管理 ====================

@router.post("/index/create")
async def create_index(
    search_service: SearchService = Depends(get_search_service),
):
    """创建 ES 索引"""
    from es import create_index as _create_index
    success = _create_index(search_service.es)
    return {
        "code": 200 if success else 500,
        "message": "索引创建成功" if success else "索引创建失败",
        "data": None,
    }


@router.post("/index/rebuild")
async def rebuild_index(
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """重建索引并全量同步数据"""
    from es import rebuild_index as _rebuild_index
    from es import sync_all_products

    # 重建索引
    success = _rebuild_index(search_service.es)
    if not success:
        return {"code": 500, "message": "索引重建失败", "data": None}

    # 全量同步
    count = sync_all_products(db, search_service.es)

    return {
        "code": 200,
        "message": f"索引重建完成，同步 {count} 条商品",
        "data": {"synced_count": count},
    }


# ==================== 课程索引管理 ====================

@router.post("/index/course/create")
async def create_course_index_endpoint(
    search_service: SearchService = Depends(get_search_service),
):
    """创建课程 ES 索引"""
    success = create_course_index(search_service.es)
    return {
        "code": 200 if success else 500,
        "message": "课程索引创建成功" if success else "课程索引创建失败",
        "data": None,
    }


@router.post("/index/course/rebuild")
async def rebuild_course_index_endpoint(
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """重建课程索引并全量同步数据"""
    success = rebuild_course_index(search_service.es)
    if not success:
        return {"code": 500, "message": "课程索引重建失败", "data": None}

    count = sync_all_courses(db, search_service.es)

    return {
        "code": 200,
        "message": f"课程索引重建完成，同步 {count} 条课程",
        "data": {"synced_count": count},
    }


# ==================== 数据同步触发 ====================

@router.post("/sync/product/{product_id}")
async def sync_single_product(
    product_id: int,
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """手动触发单个商品同步"""
    success = sync_product(db, product_id, search_service.es)
    return {
        "code": 200 if success else 500,
        "message": "同步成功" if success else "同步失败",
        "data": None,
    }


@router.delete("/sync/product/{product_id}")
async def delete_product_sync(
    product_id: int,
    search_service: SearchService = Depends(get_search_service),
):
    """从 ES 删除商品"""
    success = delete_product_from_es(product_id, search_service.es)
    return {
        "code": 200 if success else 500,
        "message": "删除成功" if success else "删除失败",
        "data": None,
    }
