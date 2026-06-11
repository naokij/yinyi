"""
印忆 (YinYi) - 照片记忆打印助手
FastAPI 后端主入口（同时托管前端 dist 静态资源）
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"[配置] 加载环境变量: {env_path}")
load_dotenv(env_path)
print(f"[配置] AI_BACKEND = {os.getenv('AI_BACKEND', 'not set')}")

from config import settings
from database import init_db
from routers import photos, analyze, export, scanner
from cache_manager import get_cache_manager, format_size


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    from database import SessionLocal, Photo as PhotoModel
    db = SessionLocal()
    try:
        stuck_photos = db.query(PhotoModel).filter(PhotoModel.status == "analyzing").all()
        if stuck_photos:
            for photo in stuck_photos:
                photo.status = "pending"
            db.commit()
            print(f"[启动] 重置 {len(stuck_photos)} 张卡住的照片状态为 pending")
    except Exception as e:
        print(f"[启动] 重置照片状态失败: {e}")
    finally:
        db.close()

    print(f"[启动] 印忆服务启动成功 (AI_BACKEND={os.getenv('AI_BACKEND', 'not set')})")
    yield
    print("[关闭] 印忆服务已关闭")


app = FastAPI(
    title="印忆 API",
    description="AI 照片精选与打印服务",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(photos.router, prefix="/api/photos", tags=["照片管理"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["AI分析"])
app.include_router(export.router, prefix="/api/export", tags=["导出打印"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["扫描任务"])


# 静态文件（导出文件）
exports_dir = settings.EXPORTS_DIR
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


# 前端 dist 静态资源
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    for fname in ("logo.svg", "favicon.ico"):
        if (FRONTEND_DIST / fname).exists():
            app.mount(f"/{fname}", StaticFiles(directory=str(FRONTEND_DIST), html=False), name=fname)


# 系统端点（必须在 SPA fallback 之前声明）
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}


@app.get("/api/info", include_in_schema=False)
async def api_info():
    return {
        "message": "欢迎使用印忆 (YinYi)",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/admin/cache/stats", include_in_schema=False)
async def get_cache_stats():
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


@app.post("/admin/cache/cleanup", include_in_schema=False)
async def trigger_cache_cleanup(force: bool = False):
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


# SPA History Mode fallback（最后声明，避免抢匹配）
INDEX_HTML = FRONTEND_DIST / "index.html"


@app.get("/", include_in_schema=False)
async def root():
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    raise HTTPException(status_code=503, detail="Frontend not built. Run: cd frontend && npm run build")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    if full_path.startswith(("api", "exports", "docs", "openapi.json", "redoc", "admin", "assets", "health", "logo.svg", "favicon.ico")):
        raise HTTPException(status_code=404, detail="Not Found")
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
