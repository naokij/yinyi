"""
HEIC 缓存管理模块
"""

import os
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class CacheStats:
    """缓存统计信息"""
    total_size: int  # 字节
    file_count: int
    oldest_file: Optional[Path]
    newest_file: Optional[Path]


class HEICCacheManager:
    """
    HEIC 缓存管理器
    
    功能：
    1. 自动清理超过大小限制的缓存
    2. 自动清理超过时间限制的缓存
    3. 统计缓存使用情况
    """
    
    def __init__(
        self,
        cache_dir: Path,
        max_size_gb: float = 5.0,
        max_age_days: int = 30,
        cleanup_interval_hours: int = 24,
        target_size_gb: float = 4.0  # 清理后的目标大小
    ):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.max_age_seconds = max_age_days * 24 * 3600
        self.cleanup_interval_seconds = cleanup_interval_hours * 3600
        self.target_size_bytes = target_size_gb * 1024 * 1024 * 1024
        
        self._last_cleanup = 0
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计信息"""
        total_size = 0
        file_count = 0
        oldest_time = float('inf')
        newest_time = 0
        oldest_file = None
        newest_file = None
        
        for file_path in self.cache_dir.glob("*.jpg"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime
                    
                    total_size += size
                    file_count += 1
                    
                    if mtime < oldest_time:
                        oldest_time = mtime
                        oldest_file = file_path
                    
                    if mtime > newest_time:
                        newest_time = mtime
                        newest_file = file_path
                        
                except (OSError, FileNotFoundError):
                    continue
        
        return CacheStats(
            total_size=total_size,
            file_count=file_count,
            oldest_file=oldest_file,
            newest_file=newest_file
        )
    
    def cleanup_if_needed(self, force: bool = False) -> dict:
        """
        如果需要，执行缓存清理
        
        Returns:
            清理结果统计
        """
        current_time = time.time()
        
        # 检查是否需要清理（按时间间隔）
        if not force and (current_time - self._last_cleanup) < self.cleanup_interval_seconds:
            return {"cleaned": False, "reason": "interval_not_met"}
        
        with self._lock:
            # 双重检查
            if not force and (current_time - self._last_cleanup) < self.cleanup_interval_seconds:
                return {"cleaned": False, "reason": "interval_not_met"}
            
            stats = self.get_stats()
            
            # 如果缓存为空
            if stats.file_count == 0:
                self._last_cleanup = current_time
                return {"cleaned": False, "reason": "cache_empty"}
            
            result = {
                "cleaned": False,
                "files_deleted": 0,
                "bytes_freed": 0,
                "reason": ""
            }
            
            # 1. 按时间清理（删除超过 max_age_days 的文件）
            files_to_delete = []
            for file_path in self.cache_dir.glob("*.jpg"):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        if current_time - mtime > self.max_age_seconds:
                            files_to_delete.append((file_path, mtime))
                    except (OSError, FileNotFoundError):
                        continue
            
            # 按修改时间排序，先删除最旧的
            files_to_delete.sort(key=lambda x: x[1])
            
            for file_path, _ in files_to_delete:
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    result["files_deleted"] += 1
                    result["bytes_freed"] += size
                except (OSError, FileNotFoundError):
                    continue
            
            # 2. 按大小清理（如果仍然超过限制）
            if stats.total_size - result["bytes_freed"] > self.max_size_bytes:
                # 重新获取剩余文件
                remaining_files = []
                for file_path in self.cache_dir.glob("*.jpg"):
                    if file_path.is_file():
                        try:
                            stat = file_path.stat()
                            remaining_files.append((file_path, stat.st_mtime, stat.st_size))
                        except (OSError, FileNotFoundError):
                            continue
                
                # 按修改时间排序（最旧的在前面）
                remaining_files.sort(key=lambda x: x[1])
                
                current_size = sum(f[2] for f in remaining_files)
                
                for file_path, _, size in remaining_files:
                    if current_size <= self.target_size_bytes:
                        break
                    
                    try:
                        file_path.unlink()
                        result["files_deleted"] += 1
                        result["bytes_freed"] += size
                        current_size -= size
                    except (OSError, FileNotFoundError):
                        continue
            
            self._last_cleanup = current_time
            result["cleaned"] = result["files_deleted"] > 0
            result["current_size_mb"] = round((stats.total_size - result["bytes_freed"]) / (1024 * 1024), 2)
            
            return result
    
    def update_access_time(self, file_path: Path):
        """更新文件访问时间（用于 LRU 策略）"""
        try:
            current_time = time.time()
            os.utime(file_path, (current_time, current_time))
        except (OSError, FileNotFoundError):
            pass
    
    def get_cache_path(self, photo_id: int) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{photo_id}.jpg"
    
    def cleanup_async(self):
        """异步执行清理（不阻塞主线程）"""
        self._executor.submit(self.cleanup_if_needed)


# 全局缓存管理器实例（懒加载）
_cache_manager: Optional[HEICCacheManager] = None

def get_cache_manager(cache_dir: Optional[Path] = None) -> HEICCacheManager:
    """
    获取缓存管理器实例
    
    Args:
        cache_dir: 缓存目录，如果为 None 则使用默认路径
    """
    global _cache_manager
    
    if _cache_manager is None:
        if cache_dir is None:
            # 默认路径：backend/data/cache/heic
            cache_dir = Path(__file__).parent / "data" / "cache" / "heic"
        
        _cache_manager = HEICCacheManager(
            cache_dir=cache_dir,
            max_size_gb=5.0,
            max_age_days=30,
            cleanup_interval_hours=24,
            target_size_gb=4.0
        )
    
    return _cache_manager


def format_size(size_bytes: float) -> str:
    """格式化字节大小为人类可读格式"""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


if __name__ == "__main__":
    # 测试代码
    import sys
    
    # 使用命令行参数指定缓存目录，或使用默认目录
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
    else:
        test_dir = Path(__file__).parent / "data" / "cache" / "heic"
    
    print(f"HEIC 缓存管理器测试")
    print(f"缓存目录: {test_dir}")
    print("-" * 50)
    
    manager = HEICCacheManager(
        cache_dir=test_dir,
        max_size_gb=5.0,
        max_age_days=30,
        cleanup_interval_hours=24
    )
    
    # 获取统计信息
    stats = manager.get_stats()
    print(f"缓存统计:")
    print(f"  文件数: {stats.file_count}")
    print(f"  总大小: {format_size(stats.total_size)}")
    if stats.oldest_file:
        print(f"  最旧文件: {stats.oldest_file.name}")
    if stats.newest_file:
        print(f"  最新文件: {stats.newest_file.name}")
    
    print("-" * 50)
    print("执行清理...")
    result = manager.cleanup_if_needed(force=True)
    
    print(f"清理结果:")
    print(f"  是否清理: {result['cleaned']}")
    print(f"  删除文件数: {result.get('files_deleted', 0)}")
    print(f"  释放空间: {format_size(result.get('bytes_freed', 0))}")
    print(f"  当前大小: {result.get('current_size_mb', 0)} MB")
    print(f"  原因: {result.get('reason', 'N/A')}")
