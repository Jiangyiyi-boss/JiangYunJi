"""
诊断脚本：检查"花瓶"和"台式花瓶"在 MySQL 和 ES 中的实际状态

服务器上执行（两种方式任选一种）：
  1) cd /app && python -m scripts.diagnose_suggest 花
  2) docker exec jyj-backend bash -c "cd /app && python -m scripts.diagnose_suggest 花"
"""
import sys
import os

# 确保能找到 /app 下的模块
sys.path.insert(0, "/app")

from database import SessionLocal
from models import Product
from es import SearchService
from sqlalchemy import or_, func


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else "花"

    print("=" * 80)
    print(f"诊断：搜索关键词 '{prefix}' 在 MySQL 和 ES 中的状态")
    print("=" * 80)

    # 1. MySQL 查询
    print("\n【1. MySQL 数据库查询】")
    print("-" * 80)
    db = SessionLocal()
    try:
        # 所有包含关键词的商品（不限 status）
        all_results = db.query(
            Product.id, Product.name, Product.status
        ).filter(
            Product.name.like(f"%{prefix}%")
        ).all()

        print(f"数据库中所有 name LIKE '%{prefix}%' 的商品: 共 {len(all_results)} 条\n")

        for row in all_results:
            print(f"  ID={row[0]:<4}  status={row[1]:<12}  name={row[2]}")

        # 只看 approved 的
        approved_results = [r for r in all_results if r[1] == "approved"]
        print(f"\n其中 status='approved' 的商品: {len(approved_results)} 条")
        for row in approved_results:
            print(f"  ID={row[0]:<4}  name={row[2]}")
    finally:
        db.close()

    # 2. ES 查询
    print("\n【2. Elasticsearch 索引查询】")
    print("-" * 80)
    try:
        es = SearchService()
        # 检查索引是否存在
        if not es.es.indices.exists(index=es.index):
            print(f"索引 {es.index} 不存在！需要重建。")
            return
        # 索引总文档数
        count_resp = es.es.count(index=es.index)
        print(f"索引 {es.index} 总文档数: {count_resp['count']}\n")

        # match 查询
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
        response = es.es.search(index=es.index, body=search_body)
        es_total = response["hits"]["total"]["value"]
        print(f"match 查询 (status=approved) 命中: {es_total} 条\n")

        for hit in response["hits"]["hits"]:
            print(f"  ID={hit['_source'].get('id'):<4}  status={hit['_source'].get('status'):<12}  "
                  f"name={hit['_source'].get('name')}  _score={hit.get('_score')}")

        # 列出所有包含"花"字的文档（不限 status）
        print("\n--- 索引中所有 name 含'花'字的文档（不限 status）---")
        all_body = {
            "query": {"match": {"name": prefix}},
            "size": 20,
            "_source": ["id", "name", "status"],
        }
        all_resp = es.es.search(index=es.index, body=all_body)
        for hit in all_resp["hits"]["hits"]:
            print(f"  ID={hit['_source'].get('id'):<4}  status={hit['_source'].get('status'):<12}  "
                  f"name={hit['_source'].get('name')}")
    except Exception as e:
        print(f"ES 查询失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
