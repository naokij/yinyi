"""
扫描任务路由
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import threading
from datetime import datetime

from database import get_db
from scanner import scan_directory_task, get_scanner_status
from ai_analyzer import get_analyzer_status


router = APIRouter()


# 分析时间统计（用于估算剩余时间）
_analyze_stats = {
    "recent_times": [],  # 最近的分析时间列表（秒）
    "lock": threading.Lock()
}


def record_analyze_time(duration_seconds: float):
    """记录分析时间（由 ai_analyzer.py 调用）"""
    with _analyze_stats["lock"]:
        _analyze_stats["recent_times"].append(duration_seconds)
        # 只保留最近 10 次
        if len(_analyze_stats["recent_times"]) > 10:
            _analyze_stats["recent_times"] = _analyze_stats["recent_times"][-10:]


def get_average_analyze_time():
    """获取平均分析时间（秒）"""
    with _analyze_stats["lock"]:
        if not _analyze_stats["recent_times"]:
            return None
        return sum(_analyze_stats["recent_times"]) / len(_analyze_stats["recent_times"])


class ScanRequest(BaseModel):
    path: Optional[str] = None
    recursive: bool = True
    check_modified: bool = True


class ScanStatus(BaseModel):
    status: str  # 综合状态: idle, scanning, analyzing
    scanner_status: str = "idle"  # 扫描器状态: idle, scanning, completed
    analyzer_status: str = "idle"  # 分析器状态: idle, analyzing
    total_photos: int
    new_photos: int
    pending: int
    duplicate_photos: int
    analyzing: int
    analyzed: int
    # 预估剩余时间
    avg_analyze_time: Optional[float] = None  # 平均分析时间（秒）
    estimated_remaining_seconds: Optional[float] = None  # 预估剩余时间（秒）


@router.post("/start", response_model=dict)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """启动扫描任务"""
    background_tasks.add_task(
        scan_directory_task,
        path=request.path,
        recursive=request.recursive,
        check_modified=request.check_modified
    )
    
    return {"message": "扫描任务已启动", "path": request.path or "默认目录"}


@router.get("/status", response_model=ScanStatus)
async def get_scan_status(db: Session = Depends(get_db)):
    """获取扫描和分析状态"""
    from database import Photo as PhotoModel
    
    total = db.query(PhotoModel).count()
    new = db.query(PhotoModel).filter(PhotoModel.status == "pending").count()
    duplicate = db.query(PhotoModel).filter(PhotoModel.status == "duplicate").count()
    analyzing = db.query(PhotoModel).filter(PhotoModel.status == "analyzing").count()
    analyzed = db.query(PhotoModel).filter(PhotoModel.status == "analyzed").count()
    
    # 获取真实的扫描器状态
    scanner_status = get_scanner_status()
    # 获取真实的分析器状态
    analyzer_status = get_analyzer_status()
    
    # 综合状态：扫描进行中 或 分析进行中
    if scanner_status["status"] == "scanning":
        overall_status = "scanning"
    elif analyzer_status["status"] == "analyzing":
        overall_status = "analyzing"
    else:
        overall_status = "idle"
    
    # 计算预估剩余时间
    avg_time = get_average_analyze_time()
    estimated_remaining = None
    if avg_time and new > 0:
        estimated_remaining = avg_time * new
    
    return ScanStatus(
        status=overall_status,
        scanner_status=scanner_status["status"],
        analyzer_status=analyzer_status["status"],
        total_photos=total,
        new_photos=new,
        pending=new,
        duplicate_photos=duplicate,
        analyzing=analyzing,
        analyzed=analyzed,
        avg_analyze_time=round(avg_time, 1) if avg_time else None,
        estimated_remaining_seconds=round(estimated_remaining, 1) if estimated_remaining else None
    )


@router.post("/stop")
async def stop_scan():
    """停止扫描任务"""
    return {"message": "扫描停止功能开发中"}
