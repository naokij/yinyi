"""
扫描任务路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from scanner import scan_directory_task


router = APIRouter()


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
    
    return ScanStatus(
        status="running" if new > 0 or analyzing > 0 else "idle",
        total_photos=total,
        new_photos=new,
        pending=new,  # 待分析数量
        duplicate_photos=duplicate,
        analyzing=analyzing,
        analyzed=analyzed
    )


@router.post("/stop")
async def stop_scan():
    """停止扫描任务"""
    # TODO: 实现任务取消机制
    return {"message": "扫描停止功能开发中"}
