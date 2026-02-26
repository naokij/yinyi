"""
导出打印路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path

from database import get_db, Photo as PhotoModel, Export as ExportModel
from renderer import render_polaroid
from config import settings


router = APIRouter()


class ExportRequest(BaseModel):
    photo_id: int
    template: str = "polaroid"  # polaroid, classic
    caption: Optional[str] = None  # 自定义文案（覆盖 AI 生成）
    include_date: bool = True
    include_location: bool = True
    # 裁切参数 (0-1 范围，表示裁切框中心位置)
    crop_x: float = 0.5  # 0=左, 0.5=中, 1=右
    crop_y: float = 0.5  # 0=上, 0.5=中, 1=下
    crop_scale: float = 1.0  # 裁切范围，1.0=充满，>1=缩小显示更多内容


class BatchExportRequest(BaseModel):
    photo_ids: List[int]
    template: str = "polaroid"
    output_format: str = "png"  # png, pdf


@router.post("/preview")
async def preview_export(request: ExportRequest, db: Session = Depends(get_db)):
    """生成打印预览图"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == request.photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 检查照片是否已分析
    if photo.status != "analyzed":
        raise HTTPException(status_code=400, detail="照片尚未完成 AI 分析")
    
    try:
        # 生成预览图
        output_path = render_polaroid(
            photo_path=photo.path,
            caption=request.caption or (photo.analysis.caption if photo.analysis else None),
            taken_at=photo.taken_at,
            location=photo.location if request.include_location else None,
            output_dir=settings.EXPORTS_DIR,
            preview=True,
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_scale=request.crop_scale
        )
        
        return FileResponse(output_path, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")


@router.post("/single", response_model=dict)
async def export_single(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """导出单张打印图"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == request.photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    if photo.status != "analyzed":
        raise HTTPException(status_code=400, detail="照片尚未完成 AI 分析")
    
    try:
        output_path = render_polaroid(
            photo_path=photo.path,
            caption=request.caption or (photo.analysis.caption if photo.analysis else None),
            taken_at=photo.taken_at,
            location=photo.location if request.include_location else None,
            output_dir=settings.EXPORTS_DIR,
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_scale=request.crop_scale
        )
        
        # 记录导出
        export_record = ExportModel(
            photo_id=photo.id,
            template_type=request.template,
            export_path=output_path,
            format="png",
            settings=str(request.dict())
        )
        db.add(export_record)
        db.commit()
        
        return {
            "message": "导出成功",
            "download_url": f"/exports/{Path(output_path).name}",
            "filename": Path(output_path).name
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/batch")
async def export_batch(
    request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """批量导出（后台任务）"""
    # TODO: 实现批量导出为 ZIP 或 PDF
    return {"message": "批量导出功能开发中", "count": len(request.photo_ids)}


@router.get("/history")
async def get_export_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取导出历史"""
    query = db.query(ExportModel).order_by(ExportModel.created_at.desc())
    total = query.count()
    exports = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "exports": exports,
        "page": page,
        "page_size": page_size
    }
