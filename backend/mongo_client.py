from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import settings

_client = None
_db = None


def get_mongo_client() -> MongoClient:
    """获取 MongoDB 客户端单例"""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGO_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
            )
            # 测试连接
            _client.admin.command("ping")
            print(f"MongoDB 连接成功: {settings.MONGO_URL}")
        except ConnectionFailure as e:
            print(f"MongoDB 连接失败: {e}")
            _client = None
            raise
    return _client


def get_mongo_db():
    """获取 MongoDB 数据库实例"""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[settings.MONGO_DB]
    return _db


def get_mongo_collection(collection_name: str):
    """获取 MongoDB 集合实例"""
    db = get_mongo_db()
    return db[collection_name]
