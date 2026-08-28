# 匠韵集 JiangYunJi

> 非遗文创电商与在线教育平台 —— 让非遗走进现代生活

匠韵集是一个集**非遗商品电商、匠人入驻、在线课程、定制服务、社区论坛**于一体的全栈应用，并融合 **AI 能力**：非遗文案智能生成/润色、非遗知识问答聊天助手。

## ✨ 功能特性

- **非遗商品电商**：商品浏览、Elasticsearch 全文检索、分类筛选、搜索建议、购物车、订单管理、支付宝沙箱支付
- **匠人入驻**：店铺入驻申请与审核、店铺管理、商品上架、定制服务
- **在线教育**：非遗课程发布、章节管理、学习进度跟踪
- **社区论坛**：帖子发布与评论（MongoDB 存储）
- **AI 赋能**
  - 非遗文案生成/润色：LangGraph 工作流，根据输入长度自动判断「生成」或「润色」，支持商品描述与课程简介两类文案
  - 非遗知识问答：LangChain + DeepSeek 聊天助手，SSE 流式输出
- **用户体系**：短信验证码登录（阿里云短信，Redis 限流防刷）、JWT 认证、用户/匠人双角色

## 🛠️ 技术架构

| 层次 | 技术选型 |
|---|---|
| 前端 | Vue 3 · Element Plus · Vite · Pinia · Vue Router |
| 后端 | FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| 数据存储 | MySQL 8 · Redis 7 · Elasticsearch 8（IK 中文分词）· MongoDB |
| AI | LangGraph · LangChain · DeepSeek（OpenAI 兼容协议） |
| 部署 | Docker Compose · Nginx |

## 📁 项目结构

```
jiang-yun-ji/
├── backend/                  # FastAPI 后端
│   ├── ai/                   # AI 模块
│   │   ├── copywriting/      #   ├─ 非遗文案生成/润色工作流（LangGraph）
│   │   └── chat/             #   └─ 非遗知识问答聊天助手（LangChain + SSE）
│   ├── router/               # API 路由
│   ├── crud/                 # 数据库访问层
│   ├── services/             # 业务服务（短信、支付等）
│   ├── es/                   # Elasticsearch 索引与搜索
│   ├── config.py             # 配置（全部来自环境变量）
│   └── main.py               # 应用入口
├── frontend/                 # Vue 3 前端
├── docker-compose.yml        # 生产编排（mysql/redis/es/rabbitmq/backend/nginx）
├── .env.example              # 根目录环境变量模板（docker compose 使用）
└── .gitignore
```

## 🚀 快速开始（本地开发）

### 后端

```bash
cd backend
cp .env.example .env        # 填入真实配置（数据库、Redis、DeepSeek Key 等）
pip install -r requirements.txt
python main.py              # 默认 http://localhost:8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                 # 默认 http://localhost:5173
```

## ⚙️ 环境变量

项目所有敏感配置均通过环境变量注入，**代码中不硬编码任何密钥**。

| 变量 | 说明 |
|---|---|
| `DB_*` | MySQL 连接（host/port/user/password/name） |
| `REDIS_*` | Redis 连接（短信验证码、分布式锁） |
| `ES_*` | Elasticsearch 连接（搜索索引） |
| `SECRET_KEY` / `ADMIN_SECRET_KEY` | JWT 签名密钥 / 超级管理员密钥 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（OpenAI 兼容协议） |
| `ALIPAY_APP_ID` / `ALIPAY_NOTIFY_URL` / `ALIPAY_RETURN_URL` | 支付宝沙箱参数与回调地址 |
| `MYSQL_ROOT_PASSWORD` | Docker Compose 部署时 MySQL root 密码 |

> 本地后端开发用 `backend/.env`；Docker 部署用根目录 `.env`（模板见 `.env.example`，真实文件已被 `.gitignore` 排除）。

## 🐳 Docker 部署

```bash
# 1. 在项目根目录创建 .env（参考 .env.example，缺失变量 compose 会直接报错）
cp .env.example .env

# 2. 启动全部服务
docker compose up -d

# 3. 初始化数据库表与 Elasticsearch 索引
docker compose exec backend python seed.py
# 重建 ES 索引（需要时）: POST /api/search/index/rebuild
```
