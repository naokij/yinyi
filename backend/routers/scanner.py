"""
扫描任务路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import threading

from database import get_db
from scanner import scan_directory_task


router = APIRouter()


# 批次信息存储（内存中，重启后重置）
_batch_info = {
    "target": 0,           # 批次目标数量
    "start_analyzed": 0,   # 批次开始时的已分析数量
    "lock": threading.Lock()
}


class ScanRequest(BaseModel):
    path: Optional[str] = None  # 如果为空，使用配置的 PHOTOS_DIR
    recursive: bool = True
    check_modified: bool = True


class ScanStatus(BaseModel):
    status: str
    total_photos: int
    new_photos: int
    pending: int  # 待分析数量
    duplicate_photos: int
    analyzing: int
    analyzed: int
    # 批次进度
    batch_target: int = 0
    batch_progress: int = 0
    batch_start_analyzed: int = 0


def set_batch_info(target: int, start_analyzed: int):
    """设置批次信息（由 analyze.py 调用）"""
    with _batch_info["lock"]:
        _batch_info["target"] = target
        _batch_info["start_analyzed"] = start_analyzed


def get_batch_info():
    """获取批次信息"""
    with _batch_info["lock"]:
        return {
            "target": _batch_info["target"],
            "start_analyzed": _batch_info["start_analyzed"]
        }


def clear_batch_info():
    """清除批次信息"""
    with _batch_info["lock"]:
        _batch_info["target"] = 0
        _batch_info["start_analyzed"] = 0


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
    """获取扫描状态"""
    from database import Photo as PhotoModel
    
    total = db.query(PhotoModel).count()
    new = db.query(PhotoModel).filter(PhotoModel.status == "pending").count()
    duplicate = db.query(PhotoModel).filter(PhotoModel.status == "duplicate").count()
    analyzing = db.query(PhotoModel).filter(PhotoModel.status == "analyzing").count()
    analyzed = db.query(PhotoModel).filter(PhotoModel.status == "analyzed").count()
    
    # 获取批次信息
    batch = get_batch_info()
    batch_target = batch["target"]
    batch_start = batch["start_analyzed"]
    
    # 计算批次进度
    batch_progress = 0
    if batch_target > 0 and batch_start > 0:
        batch_progress = max(0, analyzed - batch_start)
        
        # 只在批次真正完成时清除（已完成数量 >= 目标数量）
        # 或者所有分析都完成了（没有正在分析的，也没有待分析的）
        if batch_progress >= batch_target:
            # 批次完成
            clear_batch_info()
            batch_target = 0
            batch_start = 0
            batch_progress = 0
        elif analyzing == 0 and new == 0:
            # 所有分析都完成了
            clear_batch_info()
            batch_target = 0
            batch_start = 0
            batch_progress = 0
    
    return ScanStatus(
        status="running" if new > 0 or analyzing > 0 else "idle",
        total_photos=total,
        new_photos=new,
        pending=new,
        duplicate_photos=duplicate,
        analyzing=analyzing,
        analyzed=analyzed,
        batch_target=batch_target,
        batch_progress=batch_progress,
        batch_start_analyzed=batch_start
    )


@router.post("/stop")
async def stop_scan():
    """停止扫描任务"""
    # TODO: 实现任务取消机制
    return {"message": "扫描停止功能开发中"}
