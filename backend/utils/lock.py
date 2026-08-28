"""
Redis 分布式锁工具 —— 用于商品库存扣减等关键路径。

设计要点：
- 使用 Redis SET key value NX EX 原子加锁，token 为唯一值，仅持有者能释放。
- 支持阻塞等待与超时，锁默认 10 秒自动过期，防止死锁。
- Redis 不可用时自动降级为“无 Redis 锁”模式，配合数据库 SELECT FOR UPDATE 行锁兜底。
- 多商品订单按 product_id 排序后依次加锁，避免死锁。
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Generator

import redis

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TTL = 10          # 锁默认存活 10 秒
DEFAULT_LOCK_TIMEOUT = 5       # 阻塞等待最多 5 秒
DEFAULT_SLEEP = 0.05           # 抢锁轮询间隔


class RedisLock:
    """基于 Redis 的分布式锁，Redis 故障时自动降级。"""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._available = False
        try:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            self._client.ping()
            self._available = True
            logger.info("Redis 分布式锁已就绪 (%s:%s)", settings.REDIS_HOST, settings.REDIS_PORT)
        except Exception as exc:
            logger.warning("Redis 分布式锁不可用，将依赖数据库行锁兜底: %s", exc)
            self._client = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def acquire(
        self,
        key: str,
        *,
        ttl: int = DEFAULT_LOCK_TTL,
        blocking: bool = True,
        timeout: float = DEFAULT_LOCK_TIMEOUT,
    ) -> str | None:
        """
        尝试获取锁。

        Returns:
            token: 锁令牌，释放锁时需要传入；Redis 不可用时返回 None。
        """
        if not self._available or self._client is None:
            return None

        token = uuid.uuid4().hex
        full_key = f"lock:{key}"
        deadline = time.time() + timeout if blocking else time.time()

        while True:
            try:
                # NX: 仅当 key 不存在时才设置；EX: 设置过期时间（秒）
                if self._client.set(full_key, token, nx=True, ex=ttl):
                    return token
            except Exception as exc:
                logger.warning("Redis 加锁失败 key=%s: %s", full_key, exc)
                return None

            if not blocking or time.time() >= deadline:
                return None
            time.sleep(DEFAULT_SLEEP)

    def release(self, key: str, token: str | None) -> bool:
        """释放锁，仅当锁仍由当前 token 持有时才删除。"""
        if not token or not self._available or self._client is None:
            return False

        full_key = f"lock:{key}"
        # Lua 脚本保证“判断值一致”和“删除”的原子性
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            result = self._client.eval(lua_script, 1, full_key, token)
            return bool(result)
        except Exception as exc:
            logger.warning("Redis 解锁失败 key=%s: %s", full_key, exc)
            return False


# 全局单例
redis_lock = RedisLock()


@contextmanager
def product_stock_locks(
    product_ids: list[int],
    *,
    ttl: int = DEFAULT_LOCK_TTL,
    timeout: float = DEFAULT_LOCK_TIMEOUT,
) -> Generator[dict[int, str | None], None, None]:
    """
    为多个商品同时加锁，按 product_id 升序排序以避免死锁。

    Yields:
        dict[product_id, token|None]: 每个商品的锁令牌；若 Redis 不可用则为 None。
    """
    unique_ids = sorted(set(product_ids))
    tokens: dict[int, str | None] = {}

    for pid in unique_ids:
        token = redis_lock.acquire(f"stock:{pid}", ttl=ttl, blocking=True, timeout=timeout)
        tokens[pid] = token

    try:
        yield tokens
    finally:
        for pid in unique_ids:
            redis_lock.release(f"stock:{pid}", tokens.get(pid))
