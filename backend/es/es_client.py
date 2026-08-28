"""
Elasticsearch 客户端配置
"""
from elasticsearch import Elasticsearch
from config import settings


def get_es_client() -> Elasticsearch:
    """创建 Elasticsearch 客户端"""
    return Elasticsearch(
        hosts=[settings.ES_URL],
        request_timeout=settings.ES_TIMEOUT,
        verify_certs=False,
    )


es_client = get_es_client()
