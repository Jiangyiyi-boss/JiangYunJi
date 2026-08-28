"""
阿里云短信服务 — 短信验证码发送与校验
验证码存储在 Redis 中，支持多进程共享、服务重启不丢失、自带 TTL 过期。
"""
import random
import time
import json
import redis
from config import settings


MAX_DAILY_SMS = 5  # 单日最大发送次数
CODE_TTL = 300     # 验证码有效期 5 分钟

_redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    socket_timeout=2,
)


def _code_key(phone: str, purpose: str) -> str:
    return f"sms:code:{phone}:{purpose}"


def _count_key(phone: str, today: str) -> str:
    return f"sms:count:{phone}:{today}"


def send_sms_code(phone: str, purpose: str = "login") -> dict:
    """发送短信验证码，不同用途(purpose)的验证码独立存储"""
    today = time.strftime("%Y%m%d")

    # 检查每日限制
    count_key = _count_key(phone, today)
    try:
        count = int(_redis.get(count_key) or 0)
    except Exception:
        count = 0
    if count >= MAX_DAILY_SMS:
        return {"success": False, "message": f"今日发送次数已达上限（{MAX_DAILY_SMS}次），请明日再试"}

    # 检查60秒内是否已发送（验证码剩余有效期 > 240秒说明发送不到60秒）
    code_key = _code_key(phone, purpose)
    try:
        ttl = _redis.ttl(code_key)
    except Exception:
        ttl = -2
    if ttl > 240:
        return {"success": True, "message": "验证码已发送，请稍后重试"}

    # 生成6位验证码
    code = str(random.randint(100000, 999999))

    # 通过阿里云发送短信，失败则直接返回错误
    if not _send_via_aliyun(phone, code):
        return {"success": False, "message": "短信发送失败，请稍后重试"}

    # 发送成功，存入验证码（5分钟自动过期）并更新今日计数
    try:
        _redis.setex(code_key, CODE_TTL, code)
        _redis.incr(count_key)
        _redis.expire(count_key, 86400)  # 计数 key 24小时后自动清理
    except Exception as e:
        print(f"[SMS] Redis 写入失败: {e}")

    return {"success": True, "message": "验证码已发送"}


def verify_sms_code(phone: str, code: str, purpose: str = "login", consume: bool = True) -> bool:
    """校验短信验证码，不同用途的验证码独立校验。
    consume=True 时验证成功后删除验证码（一次性使用），
    consume=False 时仅校验不删除，保留给后续步骤使用。"""
    code_key = _code_key(phone, purpose)
    try:
        stored = _redis.get(code_key)
    except Exception:
        return False
    if stored and stored == code:
        if consume:
            try:
                _redis.delete(code_key)
            except Exception:
                pass
        return True
    return False


def _send_via_aliyun(phone: str, code: str) -> bool:
    """通过阿里云速通互联 SDK 发送短信验证码"""
    try:
        from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
        from alibabacloud_tea_util import models as util_models

        config = open_api_models.Config(
            access_key_id=settings.SMS_ACCESS_KEY_ID,
            access_key_secret=settings.SMS_ACCESS_KEY_SECRET,
        )
        config.endpoint = 'dypnsapi.aliyuncs.com'
        client = DypnsapiClient(config)

        # 速通互联模板参数格式：JSON 字符串，需包含模板中所有变量
        request = dypnsapi_models.SendSmsVerifyCodeRequest(
            phone_number=phone,
            sign_name=settings.SMS_SIGN_NAME,
            template_code=settings.SMS_TEMPLATE_CODE,
            template_param=json.dumps({"code": code, "min": "5"}),
        )
        runtime = util_models.RuntimeOptions()
        resp = client.send_sms_verify_code_with_options(request, runtime)

        # 检查响应
        if resp and resp.body and resp.body.code == "OK":
            return True
        else:
            error_msg = resp.body.message if resp and resp.body else "unknown"
            error_code = resp.body.code if resp and resp.body else "unknown"
            print(f"[SMS] 阿里云返回错误: code={error_code}, message={error_msg}")
            return False
    except Exception as e:
        print(f"[SMS] 阿里云发送失败: {e}")
        return False
