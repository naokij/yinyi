"""
照片管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Photo as PhotoModel, Analysis as AnalysisModel


router = APIRouter()


class PhotoResponse(BaseModel):
    id: int
    path: str
    filename: str
    width: Optional[int]
    height: Optional[int]
    taken_at: Optional[datetime]
    location: Optional[str]
    status: str
    memory_score: Optional[float]
    aesthetic_score: Optional[float]
    caption: Optional[str]
    
    class Config:
        from_attributes = True


class PhotoListResponse(BaseModel):
    total: int
    photos: List[PhotoResponse]
    page: int
    page_size: int


@router.get("/", response_model=PhotoListResponse)
async def list_photos(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("taken_at", regex="^(taken_at|scanned_at|memory_score|aesthetic_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取照片列表"""
    query = db.query(PhotoModel)
    
    if status:
        query = query.filter(PhotoModel.status == status)
    
    total = query.count()
    
    # 排序
    if sort_by == "memory_score":
        query = query.outerjoin(AnalysisModel).order_by(
            AnalysisModel.memory_score.desc() if sort_order == "desc" else AnalysisModel.memory_score.asc()
        )
    elif sort_by == "aesthetic_score":
        query = query.outerjoin(AnalysisModel).order_by(
            AnalysisModel.aesthetic_score.desc() if sort_order == "desc" else AnalysisModel.aesthetic_score.asc()
        )
    else:
        order_col = getattr(PhotoModel, sort_by)
        query = query.order_by(order_col.desc() if sort_order == "desc" else order_col.asc())
    
    photos = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "photos": photos,
        "page": page,
        "page_size": page_size
    }


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """获取单张照片详情"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return photo


@router.delete("/{photo_id}")
async def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """删除照片记录（不删除文件）"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 级联删除分析结果
    if photo.analysis:
        db.delete(photo.analysis)
    
    db.delete(photo)
    db.commit()
    
    return {"message": "照片记录已删除"}


@router.get("/{photo_id}/thumbnail")
async def get_thumbnail(photo_id: int, size: int = Query(300, ge=50, le=800), db: Session = Depends(get_db)):
    """获取照片缩略图"""
    # TODO: 实现缩略图生成和缓存
    pass
