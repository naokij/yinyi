"""
配置管理
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/yinyi.db"
    
    # 目录配置
    PHOTOS_DIR: str = "./photos"
    EXPORTS_DIR: str = "./exports"
    FONTS_DIR: str = "./fonts"
    TEMPLATES_DIR: str = "./templates"
    
    # AI 服务配置
    VLLM_HOST: str = "http://localhost:8000"
    VLLM_MODEL: str = "Qwen/Qwen3-VL-4B-Instruct"
    
    # 扫描配置
    SUPPORTED_FORMATS: tuple = ('.jpg', '.jpeg', '.png', '.heic', '.raw', '.cr2', '.nef')
    
    # 打印模板配置（米家 6 寸：100×148mm @ 300 DPI）
    PRINT_WIDTH_MM: int = 100
    PRINT_HEIGHT_MM: int = 148
    PRINT_DPI: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def print_width_px(self) -> int:
        """打印宽度像素"""
        return int(self.PRINT_WIDTH_MM * self.PRINT_DPI / 25.4)
    
    @property
    def print_height_px(self) -> int:
        """打印高度像素"""
        return int(self.PRINT_HEIGHT_MM * self.PRINT_DPI / 25.4)


settings = Settings()
