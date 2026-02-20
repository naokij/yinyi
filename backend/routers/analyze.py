"""
AI 分析路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db, Photo as PhotoModel, Analysis as AnalysisModel
from ai_analyzer import analyze_photo_task


router = APIRouter()


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
            # 跳过正在分析的照片，避免重复添加
            currently_analyzing.append(photo.id)
        else:
            to_analyze.append(photo.id)
            photo.status = "pending"
    
    db.commit()
    
    # 更新批次信息（累加实际加入队列的数量）
    if len(to_analyze) > 0:
        from routers.scanner import get_batch_info, set_batch_info
        
        current_batch = get_batch_info()
        current_analyzed = db.query(PhotoModel).filter(PhotoModel.status == "analyzed").count()
        
        if current_batch["target"] > 0:
            # 已有批次，累加本次实际加入的数量
            new_target = current_batch["target"] + len(to_analyze)
            set_batch_info(
                target=new_target,
                start_analyzed=current_batch["start_analyzed"]
            )
        else:
            # 新批次
            set_batch_info(
                target=len(to_analyze),
                start_analyzed=current_analyzed
            )
    
    # 启动后台分析任务
    for photo_id in to_analyze:
        background_tasks.add_task(analyze_photo_task, photo_id)
    
    return {
        "message": "分析任务已启动",
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
    
    photo.status = "pending"
    db.commit()
    
    # 启动后台任务
    background_tasks.add_task(analyze_photo_task, photo_id)
    
    return {"message": "重新分析任务已启动", "photo_id": photo_id}


@router.get("/queue/status")
async def get_queue_status():
    """获取分析队列状态"""
    # TODO: 实现任务队列状态监控
    return {"status": "not_implemented"}
