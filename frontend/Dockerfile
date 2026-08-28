# ==================== 匠韵集前端 — Dockerfile（多阶段构建）====================

# ------ 阶段 1: 构建 ------
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmmirror.com && npm ci

COPY . .
ENV NODE_OPTIONS=--max-old-space-size=1536
RUN npm run build

# ------ 阶段 2: Nginx 服务 ------
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
