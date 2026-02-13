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

# 加载环境变量
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"[配置] 加载环境变量: {env_path}")
load_dotenv(env_path)
print(f"[配置] AI_BACKEND = {os.getenv('AI_BACKEND', 'not set')}")

from config import settings
from database import init_db
from routers import photos, analyze, export, scanner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print(f"[启动] 印忆后端服务启动成功 (AI_BACKEND={os.getenv('AI_BACKEND', 'not set')})")
    yield
    # 关闭时的清理
    print("[关闭] 印忆后端服务已关闭")


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


@app.get("/admin/cache/stats")
async def get_cache_stats():
    """获取 HEIC 缓存统计信息"""
    from pathlib import Path
    from cache_manager import get_cache_manager, format_size
    
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()
    
    return {
        "total_size_bytes": stats.total_size,
        "total_size": format_size(stats.total_size),
        "file_count": stats.file_count,
        "cache_dir": str(cache_manager.cache_dir),
        "max_size": format_size(cache_manager.max_size_bytes),
        "target_size": format_size(cache_manager.target_size_bytes),
        "oldest_file": stats.oldest_file.name if stats.oldest_file else None,
        "newest_file": stats.newest_file.name if stats.newest_file else None
    }


@app.post("/admin/cache/cleanup")
async def trigger_cache_cleanup(force: bool = False):
    """手动触发缓存清理"""
    from cache_manager import get_cache_manager, format_size
    
    cache_manager = get_cache_manager()
    result = cache_manager.cleanup_if_needed(force=force)
    
    return {
        "cleaned": result["cleaned"],
        "files_deleted": result.get("files_deleted", 0),
        "bytes_freed": result.get("bytes_freed", 0),
        "freed_size": format_size(result.get("bytes_freed", 0)),
        "current_size_mb": result.get("current_size_mb", 0),
        "reason": result.get("reason", "")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
