"""
配置管理
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# 先加载环境变量（确保 .env 覆盖系统环境变量）
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(str(env_path), override=True)

# 确保环境变量已设置（pydantic-settings 会读取这些）
os.environ["AI_BACKEND"] = os.getenv("AI_BACKEND", "ollama")
os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", "http://localhost:11434")

from pydantic_settings import BaseSettings


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
    
    # Ollama 配置（Windows 原生部署）
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3-vl:4b"
    AI_BACKEND: str = "ollama"
    
    # 扫描配置
    SUPPORTED_FORMATS: tuple = ('.jpg', '.jpeg', '.png', '.heic', '.raw', '.cr2', '.nef')
    
    # 打印模板配置（米家 6 寸：100×148mm @ 300 DPI）
    PRINT_WIDTH_MM: int = 100
    PRINT_HEIGHT_MM: int = 148
    PRINT_DPI: int = 300
    
    class Config:
        env_file = None
        case_sensitive = False
        extra = 'ignore'
    
    @property
    def print_width_px(self) -> int:
        """打印宽度像素"""
        return int(self.PRINT_WIDTH_MM * self.PRINT_DPI / 25.4)
    
    @property
    def print_height_px(self) -> int:
        """打印高度像素"""
        return int(self.PRINT_HEIGHT_MM * self.PRINT_DPI / 25.4)


settings = Settings()
