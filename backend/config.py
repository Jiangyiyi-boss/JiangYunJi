from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "jiangyunji"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_STOCK_TTL: int = 86400  # 库存缓存 24 小时

    # Elasticsearch
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_INDEX: str = "products"
    ES_COURSE_INDEX: str = "courses"
    ES_TIMEOUT: int = 5  # seconds

    # MongoDB
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "jiangyunji_forum"

    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_PAYMENT_TTL_MS: int = 10 * 60 * 1000  # 10 minutes

    # JWT（生产环境必须通过环境变量/backend/.env 提供强密钥）
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Admin
    ADMIN_SECRET_KEY: str = ""

    # DeepSeek AI (替代 Dify, 使用 OpenAI 兼容协议)
    DEEPSEEK_API_KEY: str = ""          # 从 .env 读取, 不硬编码
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    AI_TIMEOUT: int = 120               # AI 请求超时(秒)

    # App
    APP_NAME: str = "匠韵集"
    APP_VERSION: str = "1.0.0"

    # SMS (阿里云号码认证 — 通过环境变量覆盖，勿在此硬编码密钥)
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = "速通互联验证服务"
    SMS_TEMPLATE_CODE: str = "100001"

    # Alipay Sandbox（APP_ID 由环境变量提供，勿硬编码）
    ALIPAY_APP_ID: str = ""
    ALIPAY_APP_PRIVATE_KEY_PATH: str = "keys/app_private_key.pem"
    ALIPAY_PUBLIC_KEY_PATH: str = "keys/alipay_public_key.pem"
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_RETURN_URL: str = ""
    ALIPAY_DEBUG: bool = True

    def model_post_init(self, __context):
        # 回调地址必须显式配置（生产为服务器公网域名/IP，本地开发可用内网穿透域名）
        if not self.ALIPAY_NOTIFY_URL or not self.ALIPAY_RETURN_URL:
            raise ValueError("请在 .env / 环境变量中配置 ALIPAY_NOTIFY_URL 和 ALIPAY_RETURN_URL")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def ES_URL(self) -> str:
        return f"http://{self.ES_HOST}:{self.ES_PORT}"

    @property
    def MONGO_URL(self) -> str:
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}"

    class Config:
        env_file = Path(__file__).parent / ".env"


settings = Settings()
