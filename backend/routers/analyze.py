"""
AI 分析路由
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db, Photo as PhotoModel, Analysis as AnalysisModel
from ai_analyzer import analyze_photo_task


router = APIRouter()

# 并行 worker 数（由 ai_analyzer 的 semaphore 二次限 API 调用并发）
BATCH_WORKERS = int(os.getenv("BATCH_WORKERS", "3"))


class AnalysisResponse(BaseModel):
    id: int
    photo_id: int
    description: Optional[str]
    caption: Optional[str]
    tags: Optional[str]
    memory_score: Optional[float]
    aesthetic_score: Optional[float]
    sentiment: Optional[str]
    model: Optional[str]
    analyzed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    photo_ids: List[int]
    force_reanalyze: bool = False


@router.get("/{photo_id}", response_model=AnalysisResponse)
async def get_analysis(photo_id: int, db: Session = Depends(get_db)):
    """获取照片分析结果"""
    analysis = db.query(AnalysisModel).filter(AnalysisModel.photo_id == photo_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    return analysis


@router.post("/batch", response_model=dict)
async def batch_analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量分析照片（后台任务）"""
    photos = db.query(PhotoModel).filter(PhotoModel.id.in_(request.photo_ids)).all()
    
    if len(photos) != len(request.photo_ids):
        found_ids = {p.id for p in photos}
        missing = set(request.photo_ids) - found_ids
        raise HTTPException(status_code=404, detail=f"照片不存在: {missing}")
    
    # 过滤已分析和正在分析的照片（除非强制重新分析）
    to_analyze = []
    already_analyzed = []
    currently_analyzing = []
    
    for photo in photos:
        if photo.status == "analyzed" and not request.force_reanalyze:
            already_analyzed.append(photo.id)
        elif photo.status == "analyzing":
            currently_analyzing.append(photo.id)
        else:
            to_analyze.append(photo.id)
    
    db.commit()
    
    # 启动后台并行分析任务
    def _run_in_thread_pool():
        with ThreadPoolExecutor(max_workers=BATCH_WORKERS) as pool:
            futures = [pool.submit(analyze_photo_task, pid) for pid in to_analyze]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f"[batch] 任务失败: {e}", flush=True)

    background_tasks.add_task(_run_in_thread_pool)

    return {
        "message": f"分析任务已启动（{BATCH_WORKERS} 并行）",
        "total": len(request.photo_ids),
        "queued": len(to_analyze),
        "skipped": len(already_analyzed),
        "analyzing": len(currently_analyzing),
        "skipped_ids": already_analyzed,
        "analyzing_ids": currently_analyzing
    }


@router.post("/{photo_id}/reanalyze", response_model=dict)
async def reanalyze_photo(
    photo_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """重新分析单张照片"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 删除旧分析结果
    if photo.analysis:
        db.delete(photo.analysis)
    
    db.commit()
    
    # 启动后台任务
    background_tasks.add_task(analyze_photo_task, photo_id)
    
    return {"message": "重新分析任务已启动", "photo_id": photo_id}


@router.get("/queue/status")
async def get_queue_status():
    """获取分析队列状态"""
    return {"status": "not_implemented"}


@router.post("/all", response_model=dict)
async def analyze_all_pending(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析所有待处理照片"""
    # 查询所有 pending 状态的照片
    pending_photos = db.query(PhotoModel).filter(
        PhotoModel.status == "pending"
    ).all()
    
    if len(pending_photos) == 0:
        return {
            "message": "没有待分析的照片",
            "total": 0,
            "queued": 0
        }
    
    # 启动后台并行分析任务
    pending_ids = [p.id for p in pending_photos]
    def _run_in_thread_pool():
        with ThreadPoolExecutor(max_workers=BATCH_WORKERS) as pool:
            futures = [pool.submit(analyze_photo_task, pid) for pid in pending_ids]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f"[analyze-all] 任务失败: {e}", flush=True)

    background_tasks.add_task(_run_in_thread_pool)

    return {
        "message": f"分析任务已启动（{BATCH_WORKERS} 并行，{len(pending_ids)} 张）",
        "total": len(pending_photos),
        "queued": len(pending_photos)
    }
