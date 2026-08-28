# ==================== 匠韵集后端 — Dockerfile ====================
FROM python:3.12-slim

WORKDIR /app

# 更换为国内 apt 源，加速 gcc 等系统依赖安装
RUN set -ex \
    && if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
         sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
       else \
         sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list; \
       fi

# 安装系统依赖（cryptography 需要 gcc 编译）
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制后端代码
COPY . .

# 创建上传目录（运行时实际存放位置在挂载卷中）
RUN mkdir -p uploads/videos uploads/images

EXPOSE 8000

# 使用 entrypoint 等待数据库就绪
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
