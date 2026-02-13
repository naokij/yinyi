<template>
  <div class="home">
    <header class="header">
      <h1>印忆</h1>
      <p class="subtitle">照片记忆打印助手</p>
    </header>
    
    <main class="main">
      <!-- 扫描状态卡片 -->
      <div class="card status-card">
        <h2>📸 照片库状态</h2>
        <div class="stats">
          <div class="stat-item">
            <span class="stat-value">{{ photoStore.scanStatus.total_photos }}</span>
            <span class="stat-label">总照片</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ photoStore.scanStatus.analyzed }}</span>
            <span class="stat-label">已分析</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ photoStore.scanStatus.pending }}</span>
            <span class="stat-label">待处理</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ photoStore.scanStatus.duplicate_photos }}</span>
            <span class="stat-label">重复</span>
          </div>
        </div>
        
        <div class="actions">
          <button 
            class="btn btn-primary"
            @click="startScan"
            :disabled="scanning"
          >
            {{ scanning ? '扫描中...' : '开始扫描' }}
          </button>
          <button class="btn btn-secondary" @click="goToGallery">
            浏览照片
          </button>
        </div>
      </div>
      
      <!-- 快速操作 -->
      <div class="card quick-actions">
        <h2>⚡ 快速操作</h2>
        <div class="action-list">
          <div class="action-item" @click="analyzeAll">
            <span class="icon">🤖</span>
            <div class="action-info">
              <h3>AI 分析全部</h3>
              <p>为待处理照片生成温馨文案</p>
            </div>
          </div>
          
          <div class="action-item" @click="goToHighlights">
            <span class="icon">✨</span>
            <div class="action-info">
              <h3>精选回忆</h3>
              <p>查看高回忆价值照片</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 最近导出 -->
      <div class="card">
        <h2>🖨️ 最近导出</h2>
        <p class="empty-text">暂无导出记录</p>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePhotoStore } from '@/stores/photos'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const photoStore = usePhotoStore()
    const scanning = ref(false)
    
    const pending = computed(() => 
      photoStore.scanStatus.total_photos - 
      photoStore.scanStatus.analyzed - 
      photoStore.scanStatus.duplicate_photos
    )
    
    onMounted(() => {
      photoStore.fetchPhotos()
      photoStore.pollScanStatus()
    })
    
    const startScan = async () => {
      scanning.value = true
      try {
        await photoStore.startScan()
      } finally {
        scanning.value = false
      }
    }
    
    const goToGallery = () => {
      router.push('/gallery')
    }
    
    const analyzeAll = async () => {
      // 获取所有待分析的照片
      const maxAnalyze = 10000  // 支持最多分析10000张照片
      
      // 先获取足够多的待分析照片
      await photoStore.fetchPhotos({ 
        status: 'pending', 
        page: 1, 
        page_size: maxAnalyze 
      })
      
      const pendingIds = photoStore.photos.map(p => p.id)
      if (pendingIds.length === 0) {
        alert('没有待分析的照片')
        return
      }
      
      const idsToAnalyze = pendingIds
      const totalPending = photoStore.total
      
      let confirmMsg
      confirmMsg = `确定要分析 ${totalPending} 张照片吗？这可能需要较长时间。`
      
      if (confirm(confirmMsg)) {
        await photoStore.batchAnalyze(idsToAnalyze)
        alert('分析任务已启动，请稍后查看结果')
        // 刷新照片列表
        photoStore.fetchPhotos()
      }
    }
    
    const goToHighlights = () => {
      router.push({
        path: '/gallery',
        query: { sort: 'memory_score' }
      })
    }
    
    return {
      photoStore,
      scanning,
      pending,
      startScan,
      goToGallery,
      analyzeAll,
      goToHighlights
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 20px;
  text-align: center;
}

.header h1 {
  font-size: 36px;
  font-weight: 300;
  margin-bottom: 8px;
}

.subtitle {
  opacity: 0.9;
  font-size: 14px;
}

.main {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.card h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 600;
  color: #667eea;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a6fd6;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #666;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-item:hover {
  background: #e9ecef;
}

.icon {
  font-size: 24px;
  margin-right: 16px;
}

.action-info h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.action-info p {
  font-size: 12px;
  color: #999;
}

.empty-text {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 20px;
}

@media (max-width: 480px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>
