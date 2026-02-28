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
        
        <!-- 扫描器状态 -->
        <div v-if="isScannerRunning" class="scanner-status running">
          🔄 扫描进行中...
        </div>
        <div v-else-if="photoStore.scanStatus.scanner_status === 'completed'" class="scanner-status completed">
          ✅ 扫描完成
        </div>
        
        <!-- 分析器状态 -->
        <div v-if="isAnalyzing" class="analyzer-status running">
          🤖 AI 分析进行中...
        </div>
        
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
        
        <!-- 扫描进度 -->
        <div v-if="isScannerRunning" class="progress-section scanner-progress">
          <div class="scanner-info">
            <span class="scanner-icon">🔄</span>
            <span>正在扫描...</span>
          </div>
          <p class="progress-text" v-if="photoStore.scanStatus.new_photos > 0">
            发现 {{ photoStore.scanStatus.new_photos }} 张新照片，等待分析
          </p>
          <p class="progress-text" v-else>
            扫描进行中...
          </p>
        </div>
        
        <!-- 分析进度条 -->
        <div v-if="photoStore.scanStatus.analyzing > 0" class="progress-section">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="progress-text">
            全局进度: {{ progressPercent }}% | 
            正在分析: {{ photoStore.scanStatus.analyzing }} 张
            <span v-if="estimatedTime">| 剩余时间: {{ estimatedTime }}</span>
          </p>
        </div>
        
        <div class="actions">
          <button 
            class="btn btn-primary"
            @click="startScan"
            :disabled="scanning || isScannerRunning"
          >
            {{ scanning ? '扫描中...' : isScannerRunning ? '扫描进行中' : '开始扫描' }}
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
          <div class="action-item" @click="analyzeAll" :class="{ 'disabled': isAnalyzing }">
            <span class="icon">🤖</span>
            <div class="action-info">
              <h3>{{ isAnalyzing ? '分析中...' : 'AI 分析照片' }}</h3>
              <p v-if="isAnalyzing">正在分析 {{ photoStore.scanStatus.analyzing }} 张照片...</p>
              <p v-else>待处理: {{ photoStore.scanStatus.pending }} 张照片</p>
            </div>
            <div v-if="isAnalyzing" class="spinner"></div>
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
    
    // 扫描器是否正在运行
    const isScannerRunning = computed(() => 
      photoStore.scanStatus.scanner_status === 'scanning'
    )
    
    // 分析器是否正在运行
    const isAnalyzing = computed(() => 
      photoStore.scanStatus.analyzer_status === 'analyzing'
    )
    
    // 预估剩余时间
    const estimatedTime = computed(() => {
      const seconds = photoStore.scanStatus.estimated_remaining_seconds
      if (!seconds || seconds <= 0) return null
      
      if (seconds < 60) {
        return `${Math.round(seconds)}秒`
      } else if (seconds < 3600) {
        const mins = Math.round(seconds / 60)
        return `${mins}分钟`
      } else {
        const hours = Math.floor(seconds / 3600)
        const mins = Math.round((seconds % 3600) / 60)
        return `${hours}小时${mins}分钟`
      }
    })
    
    const startPolling = () => {
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
      // 如果正在分析，禁止重复点击
      if (isAnalyzing.value) {
        showToast('分析任务正在进行中，请稍候...', 'warning')
        return
      }
      
      analyzing.value = true
      try {
        // 获取待分析照片数量
        await photoStore.pollScanStatus()
        
        const totalPending = photoStore.scanStatus.pending
        
        if (totalPending === 0) {
          showToast('没有待分析的照片', 'warning')
          return
        }
        
        const confirmMsg = `确定要分析 ${totalPending} 张待处理照片吗？\n\n分析过程中可随时关闭页面，重启后会自动继续。`
        
        if (confirm(confirmMsg)) {
          showToast('正在启动分析...', 'info')
          
          const result = await photoStore.analyzeAll()
          
          if (result.queued > 0) {
            showToast(`已启动分析 ${result.queued} 张照片`, 'success')
          }
          
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
      isAnalyzing,
      isScannerRunning,
      pending,
      progressPercent,
      estimatedTime,
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

.scanner-status {
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.scanner-status.running {
  background: #e8f5e9;
  color: #2e7d32;
  animation: pulse 2s infinite;
}

.scanner-status.completed {
  background: #e3f2fd;
  color: #1565c0;
}

.analyzer-status {
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.analyzer-status.running {
  background: #fce4ec;
  color: #c2185b;
  animation: pulse 2s infinite;
}

.scanner-progress {
  background: #fff3e0;
  border-radius: 8px;
  padding: 12px;
}

.scanner-progress .scanner-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #e65100;
  margin-bottom: 4px;
}

.scanner-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
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
