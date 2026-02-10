"""
印忆 (YinYi) - 照片记忆打印助手
FastAPI 后端主入口
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from config import settings
from database import init_db
from routers import photos, analyze, export, scanner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print("🚀 印忆后端服务启动成功")
    yield
    # 关闭时的清理
    print("👋 印忆后端服务已关闭")


app = FastAPI(
    title="印忆 API",
    description="AI 照片精选与打印服务",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(photos.router, prefix="/api/photos", tags=["照片管理"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["AI分析"])
app.include_router(export.router, prefix="/api/export", tags=["导出打印"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["扫描任务"])

# 静态文件服务（导出文件）
exports_dir = settings.EXPORTS_DIR
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


@app.get("/")
async def root():
    return {
        "message": "欢迎使用印忆 (YinYi)",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
