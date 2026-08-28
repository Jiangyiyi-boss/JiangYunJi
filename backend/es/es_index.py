"""
Elasticsearch 索引管理
"""
import logging
from elasticsearch import Elasticsearch
from config import settings

logger = logging.getLogger(__name__)

PRODUCT_INDEX = settings.ES_INDEX
COURSE_INDEX = settings.ES_COURSE_INDEX

PRODUCT_MAPPING = {
    "settings": {
        "index": {
            "number_of_replicas": 0  # 单节点部署，不需要副本分片
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},  # 商品ID，整数类型
            "name": {  # 商品名称，全文检索字段
                "type": "text",
                "analyzer": "ik_max_word",       # 索引时：最细粒度分词（如"景德镇花瓶"→"景德镇/景德/镇/花瓶/花/瓶"）
                "search_analyzer": "ik_smart",   # 搜索时：最粗粒度分词（如"景德镇花瓶"→"景德镇/花瓶"）
                "fields": {
                    "suggest": {  # 搜索建议专用子字段，用于自动补全
                        "type": "completion",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_max_word",
                        "preserve_separators": False,       # 不保留分隔符
                        "preserve_position_increments": False,  # 不保留位置增量
                    }
                },
            },
            "description": {  # 商品描述，全文检索字段
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "price": {"type": "float"},           # 商品价格，支持范围查询和排序
            "original_price": {"type": "float"},  # 原价
            "stock": {"type": "integer"},         # 库存数量
            "sales": {"type": "integer"},         # 销量，支持排序
            "category": {"type": "keyword"},      # 分类名称，精确匹配，不分词
            "brand": {"type": "keyword"},         # 品牌/匠人店铺名，精确匹配
            "images": {"type": "keyword"},        # 商品图片URL数组
            "status": {"type": "keyword"},        # 商品状态（approved/pending等），精确过滤
            "artisan_id": {"type": "integer"},    # 所属匠人ID
            "artisan_name": {"type": "keyword"},  # 匠人名称
            "created_at": {  # 创建时间
                "type": "date",
                "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis",  # 支持多种日期格式
            },
        }
    }
}

COURSE_MAPPING = {
    "settings": {
        "index": {
            "number_of_replicas": 0  # 单节点部署，不需要副本分片
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},  # 课程ID，整数类型
            "title": {  # 课程标题，全文检索字段
                "type": "text",
                "analyzer": "ik_max_word",       # 索引时：最细粒度分词
                "search_analyzer": "ik_smart",   # 搜索时：最粗粒度分词
            },
            "description": {  # 课程描述，全文检索字段
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "craft_intro": {  # 技艺介绍，课程独有字段，全文检索
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "price": {"type": "float"},           # 课程价格，支持范围查询和排序
            "category": {"type": "keyword"},      # 课程分类，精确匹配，不分词
            "difficulty": {"type": "keyword"},    # 难度等级（beginner/intermediate/advanced），精确过滤
            "tags": {"type": "keyword"},          # 课程标签数组，精确匹配
            "status": {"type": "keyword"},        # 课程状态（published/draft等），精确过滤
            "artisan_id": {"type": "integer"},    # 所属匠人ID
            "artisan_name": {"type": "keyword"},  # 匠人名称
            "enrolled_count": {"type": "integer"},  # 报名人数，支持排序
            "lesson_count": {"type": "integer"},    # 课时总数
            "is_free": {"type": "boolean"},       # 是否免费，布尔过滤
            "cover_image": {"type": "keyword"},   # 封面图URL
            "created_at": {  # 创建时间
                "type": "date",
                "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis",  # 支持多种日期格式
            },
        }
    }
}


def create_index(es: Elasticsearch) -> bool:
    """创建商品索引"""
    try:
        if es.indices.exists(index=PRODUCT_INDEX):
            logger.info(f"索引 {PRODUCT_INDEX} 已存在")
            return True
        es.indices.create(index=PRODUCT_INDEX, body=PRODUCT_MAPPING)
        logger.info(f"索引 {PRODUCT_INDEX} 创建成功")
        return True
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        return False


def create_course_index(es: Elasticsearch) -> bool:
    """创建课程索引"""
    try:
        if es.indices.exists(index=COURSE_INDEX):
            logger.info(f"索引 {COURSE_INDEX} 已存在")
            return True
        es.indices.create(index=COURSE_INDEX, body=COURSE_MAPPING)
        logger.info(f"索引 {COURSE_INDEX} 创建成功")
        return True
    except Exception as e:
        logger.error(f"创建课程索引失败: {e}")
        return False


def delete_index(es: Elasticsearch) -> bool:
    """删除商品索引"""
    try:
        if es.indices.exists(index=PRODUCT_INDEX):
            es.indices.delete(index=PRODUCT_INDEX)
            logger.info(f"索引 {PRODUCT_INDEX} 已删除")
        return True
    except Exception as e:
        logger.error(f"删除索引失败: {e}")
        return False


def delete_course_index(es: Elasticsearch) -> bool:
    """删除课程索引"""
    try:
        if es.indices.exists(index=COURSE_INDEX):
            es.indices.delete(index=COURSE_INDEX)
            logger.info(f"索引 {COURSE_INDEX} 已删除")
        return True
    except Exception as e:
        logger.error(f"删除课程索引失败: {e}")
        return False


def rebuild_index(es: Elasticsearch) -> bool:
    """重建索引（先删除再创建）"""
    if not delete_index(es):
        return False
    return create_index(es)


def rebuild_course_index(es: Elasticsearch) -> bool:
    """重建课程索引（先删除再创建）"""
    if not delete_course_index(es):
        return False
    return create_course_index(es)
