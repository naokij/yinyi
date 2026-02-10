"""
模型定义（Pydantic schemas）
用于 API 请求和响应的验证
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PhotoStatus(str, Enum):
    """照片状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    DUPLICATE = "duplicate"
    ERROR = "error"


class SentimentType(str, Enum):
    """情感标签枚举"""
    HAPPY = "happy"
    WARM = "warm"
    NOSTALGIC = "nostalgic"
    PEACEFUL = "peaceful"
    ROMANTIC = "romantic"
    ENERGETIC = "energetic"


class PhotoBase(BaseModel):
    """照片基础模型"""
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[datetime] = None
    location: Optional[str] = None
    camera: Optional[str] = None


class PhotoCreate(PhotoBase):
    """创建照片请求"""
    path: str
    file_hash: str
    file_size: int


class PhotoUpdate(BaseModel):
    """更新照片请求"""
    caption: Optional[str] = None
    status: Optional[PhotoStatus] = None


class PhotoInDB(PhotoBase):
    """数据库中的照片模型"""
    id: int
    path: str
    file_hash: Optional[str] = None
    status: PhotoStatus
    scanned_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisBase(BaseModel):
    """分析结果基础模型"""
    description: Optional[str] = None
    caption: Optional[str] = None
    memory_score: Optional[float] = Field(None, ge=0, le=10)
    aesthetic_score: Optional[float] = Field(None, ge=0, le=10)
    sentiment: Optional[SentimentType] = None


class AnalysisCreate(AnalysisBase):
    """创建分析结果请求"""
    photo_id: int
    tags: List[str] = []


class AnalysisInDB(AnalysisBase):
    """数据库中的分析结果模型"""
    id: int
    photo_id: int
    tags: str  # JSON 字符串
    model: Optional[str] = None
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class ExportBase(BaseModel):
    """导出记录基础模型"""
    template_type: str
    format: str


class ExportCreate(ExportBase):
    """创建导出记录请求"""
    photo_id: int
    export_path: str
    settings: Optional[str] = None


class ExportInDB(ExportBase):
    """数据库中的导出记录模型"""
    id: int
    photo_id: int
    export_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True
