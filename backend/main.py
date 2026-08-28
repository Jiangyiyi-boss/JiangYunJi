from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from config import settings
from database import engine, Base
import os
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # 初始化 RabbitMQ 延时队列（非致命错误）
    try:
        from rabbitmq import setup as rabbitmq_setup
        rabbitmq_setup()
        print("RabbitMQ queues initialized")
    except Exception as e:
        print(f"RabbitMQ setup failed (non-fatal): {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="非遗电商平台 - 匠韵集 API",
    lifespan=lifespan,
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directories exist
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/images", exist_ok=True)

# Static files for uploaded content
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Routers
from models import User, Artisan, Product, Category, Order, CartItem, Address, ProductFavorite
from models import Course, Chapter, Lesson, Enrollment, Comment, StudyNote  # Online education
from router.auth import router as auth_router
from router.users import router as users_router
from router.products import router as products_router
from router.orders import router as orders_router
from router.artisan import router as artisan_router
from router.forum_mongo import router as forum_router
from router.courses import router as courses_router
from router.payment import router as payment_router
from router.commissions import router as commissions_router
from router.banners import router as banners_router
from router.search import router as search_router
from router.workflow import router as workflow_router
from router.chat import router as chat_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(artisan_router)
app.include_router(forum_router)
app.include_router(courses_router)
app.include_router(payment_router)
app.include_router(commissions_router)
app.include_router(banners_router)
app.include_router(search_router)
app.include_router(workflow_router)
app.include_router(chat_router)


# ==================== File Upload ====================

ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB


@app.post("/api/upload/video")
async def upload_video(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="不支持的视频格式，仅支持 mp4/webm/mov/avi")
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="视频文件不能超过 500MB")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("uploads/videos", filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/static/videos/{filename}", "filename": filename}


@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 jpg/png/webp")
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片文件不能超过 10MB")
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("uploads/images", filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/static/images/{filename}", "filename": filename}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ==================== 前端静态文件服务 ====================

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

# 挂载前端静态资源（CSS/JS/图片等）
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")


@app.get("/")
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str = ""):
    """提供前端页面，支持 Vue Router history 模式"""
    if not full_path or full_path == "index.html":
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    # 尝试返回静态文件
    file_path = os.path.join(FRONTEND_DIST, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # 否则返回 index.html（Vue Router history 模式）
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="页面不存在")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)