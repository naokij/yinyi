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
            <span class="stat-value analyzing-count">{{ photoStore.scanStatus.analyzing }}</span>
            <span class="stat-label">分析中</span>
          </div>
        </div>
        
        <!-- 分析进度条 -->
        <div v-if="photoStore.scanStatus.analyzing > 0" class="progress-section">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="progress-text">
            正在分析: {{ photoStore.scanStatus.analyzing }} 张
            <span v-if="photoStore.scanStatus.pending > 0">| 剩余: {{ photoStore.scanStatus.pending }} 张</span>
          </p>
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
          <div class="action-item" @click="analyzeAll" :class="{ 'disabled': analyzing }">
            <span class="icon">🤖</span>
            <div class="action-info">
              <h3>{{ analyzing ? '分析中...' : 'AI 分析照片' }}</h3>
              <p>{{ analyzing ? `正在分析，请稍候...` : `待处理: ${photoStore.scanStatus.pending} 张照片` }}</p>
            </div>
            <div v-if="analyzing" class="spinner"></div>
          </div>
          
          <div class="action-item" @click="goToHighlights">
            <span class="icon">✨</span>
            <div class="action-info">
              <h3>精选回忆</h3>
              <p>查看高回忆价值照片</p>
            </div>
          </div>
        </div>
        
        <!-- Toast 通知 -->
        <transition name="toast">
          <div v-if="toast.show" class="toast" :class="toast.type">
            {{ toast.message }}
          </div>
        </transition>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePhotoStore } from '@/stores/photos'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const photoStore = usePhotoStore()
    const scanning = ref(false)
    const analyzing = ref(false)
    const toast = ref({ show: false, message: '', type: 'success' })
    let pollInterval = null
    
    const pending = computed(() => 
      photoStore.scanStatus.total_photos - 
      photoStore.scanStatus.analyzed - 
      photoStore.scanStatus.duplicate_photos
    )
    
    const progressPercent = computed(() => {
      const total = photoStore.scanStatus.total_photos
      const analyzed = photoStore.scanStatus.analyzed
      if (total === 0) return 0
      return Math.round((analyzed / total) * 100)
    })
    
    const startPolling = () => {
      // 如果正在分析，每 5 秒更新一次状态
      if (pollInterval) clearInterval(pollInterval)
      pollInterval = setInterval(() => {
        photoStore.pollScanStatus()
      }, 5000)
    }
    
    const stopPolling = () => {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }
    
    onMounted(() => {
      photoStore.fetchPhotos()
      photoStore.pollScanStatus()
      startPolling()
    })
    
    onUnmounted(() => {
      stopPolling()
    })
    
    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => {
        toast.value.show = false
      }, 3000)
    }
    
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
      if (analyzing.value) return
      
      analyzing.value = true
      try {
        // 获取所有待分析的照片
        const maxAnalyze = 5000  // 每次最多分析5000张照片
        
        // 先获取足够多的待分析照片
        await photoStore.fetchPhotos({ 
          status: 'pending', 
          page: 1, 
          page_size: maxAnalyze 
        })
        
        const pendingIds = photoStore.photos.map(p => p.id)
        if (pendingIds.length === 0) {
          showToast('没有待分析的照片', 'warning')
          return
        }
        
        const idsToAnalyze = pendingIds
        const totalPending = photoStore.total
        
        let confirmMsg
        if (totalPending > maxAnalyze) {
          confirmMsg = `共有 ${totalPending} 张待分析照片。\n将分析前 ${idsToAnalyze.length} 张，可多次点击继续分析。\n\n确定开始吗？`
        } else {
          confirmMsg = `确定要分析 ${totalPending} 张照片吗？`
        }
        
        if (confirm(confirmMsg)) {
          showToast('正在启动分析...', 'info')
          
          const result = await photoStore.batchAnalyze(idsToAnalyze)
          
          // 处理返回结果
          if (result.analyzing > 0) {
            showToast(`${result.analyzing} 张照片正在分析中，已跳过`, 'warning')
          } else if (result.queued > 0) {
            showToast(`已启动分析 ${result.queued} 张照片`, 'success')
          }
          
          // 刷新状态
          photoStore.pollScanStatus()
        }
      } catch (error) {
        console.error('分析失败:', error)
        showToast('启动分析失败: ' + (error.response?.data?.detail || error.message || '未知错误'), 'error')
      } finally {
        analyzing.value = false
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
      analyzing,
      pending,
      progressPercent,
      toast,
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

.analyzing-count {
  color: #f59e0b;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.progress-section {
  margin: 16px 0;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s ease;
  animation: progress-shine 2s infinite;
}

@keyframes progress-shine {
  0% { background-position: -100px 0; }
  100% { background-position: 100px 0; }
}

.progress-text {
  text-align: center;
  font-size: 13px;
  color: #666;
  margin-top: 8px;
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

.action-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #667eea;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-left: auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.toast.success {
  background: #10b981;
}

.toast.error {
  background: #ef4444;
}

.toast.warning {
  background: #f59e0b;
}

.toast.info {
  background: #3b82f6;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
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
