<template>
  <div class="print-view">
    <header class="header">
      <button class="back-btn" @click="$router.push('/gallery')">←</button>
      <h1>打印预览</h1>
    </header>
    
    <div v-if="loading" class="loading">
      加载中...
    </div>
    
    <div v-else-if="photo" class="content">
      <!-- 预览区域 -->
      <div class="preview-section">
        <!-- 标签切换 -->
        <div class="view-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: currentTab === 'original' }"
            @click="currentTab = 'original'"
          >
            原片
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: currentTab === 'preview', ready: previewReady }"
            @click="currentTab = 'preview'"
          >
            预览
            <span v-if="previewReady" class="ready-badge">✓</span>
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: currentTab === 'crop' }"
            @click="currentTab = 'crop'"
          >
            裁切调整
          </button>
        </div>
        
        <div class="preview-container">
          <!-- 原片显示 -->
          <img 
            v-if="currentTab === 'original' && originalUrl" 
            :src="originalUrl" 
            alt="原片" 
            class="preview-image"
            :style="cropPreviewStyle"
          >
          <!-- 预览图显示 -->
          <img 
            v-else-if="currentTab === 'preview' && previewUrl" 
            :src="previewUrl" 
            alt="打印预览" 
            class="preview-image"
          >
          <!-- 裁切预览 -->
          <div v-else-if="currentTab === 'crop'" class="crop-preview">
            <img 
              v-if="originalUrl" 
              :src="originalUrl" 
              alt="裁切预览" 
              class="crop-image"
              :style="cropPreviewStyle"
            >
            <div class="crop-overlay">
              <div class="crop-box" :style="cropBoxStyle"></div>
            </div>
          </div>
          <!-- 预览生成中 -->
          <div v-else-if="generating" class="preview-placeholder">
            <div class="spinner"></div>
            <p>预览生成中...</p>
          </div>
          <!-- 预览未生成 -->
          <div v-else class="preview-placeholder">
            <p>点击"生成预览"查看效果</p>
          </div>
        </div>
        
        <!-- 预览状态提示 -->
        <div class="preview-status">
          <span v-if="generating" class="status generating">
            <span class="spinner-small"></span>
            预览生成中...
          </span>
          <span v-else-if="previewReady" class="status ready">
            ✓ 预览已就绪
          </span>
          <span v-else class="status">
            点击"预览"标签查看打印效果
          </span>
        </div>
      </div>
      
        <!-- 编辑区域 -->
      <div class="edit-section">
        <div class="info-card">
          <h3>📷 照片信息</h3>
          <p><strong>文件名:</strong> {{ photo.filename }}</p>
          <p v-if="photo.taken_at">
            <strong>拍摄时间:</strong> {{ formatDate(photo.taken_at) }}
          </p>
          <p v-if="photo.location">
            <strong>地点:</strong> {{ photo.location }}
          </p>
        </div>
        
        <!-- 裁切调整 -->
        <div class="edit-card crop-card">
          <h3>✂️ 裁切调整</h3>
          <p class="hint">调整照片在模板中的显示区域</p>
          
          <div class="crop-controls">
            <div class="crop-control">
              <label>水平位置: {{ cropXLabel }}</label>
              <input 
                type="range" 
                v-model.number="cropX" 
                min="0" 
                max="1" 
                step="0.05"
                @change="onCropChange"
              >
              <div class="crop-labels">
                <span>左</span>
                <span>中</span>
                <span>右</span>
              </div>
            </div>
            
            <div class="crop-control">
              <label>垂直位置: {{ cropYLabel }}</label>
              <input 
                type="range" 
                v-model.number="cropY" 
                min="0" 
                max="1" 
                step="0.05"
                @change="onCropChange"
              >
              <div class="crop-labels">
                <span>上</span>
                <span>中</span>
                <span>下</span>
              </div>
            </div>
          </div>
          
          <button 
            class="btn btn-secondary btn-small"
            @click="resetCrop"
          >
            重置裁切
          </button>
        </div>
        
        <div class="edit-card">
          <h3>✏️ 文案编辑</h3>
          <div class="form-group">
            <label>感性文案</label>
            <textarea 
              v-model="customCaption" 
              rows="3"
              placeholder="输入你想打印的文案..."
            ></textarea>
            <p class="hint">AI 生成：{{ photo.caption || '暂无' }}</p>
          </div>
          
          <div class="form-group">
            <label class="checkbox">
              <input type="checkbox" v-model="includeDate">
              显示日期
            </label>
          </div>
          
          <div class="form-group">
            <label class="checkbox">
              <input type="checkbox" v-model="includeLocation">
              显示地点
            </label>
          </div>
        </div>
        
        <div class="actions">
          <button 
            class="btn btn-secondary"
            @click="generatePreview"
            :disabled="generating"
          >
            {{ generating ? '生成中...' : '生成预览' }}
          </button>
          <button 
            class="btn btn-primary"
            @click="exportPhoto"
            :disabled="!previewUrl || exporting"
          >
            {{ exporting ? '导出中...' : '导出打印图' }}
          </button>
        </div>
      </div>
    </div>
    
    <div v-else class="error">
      <p>照片不存在</p>
      <button @click="$router.push('/gallery')">返回照片库</button>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { photoApi, exportApi } from '@/api'

export default {
  name: 'Print',
  props: ['id'],
  setup(props) {
    const route = useRoute()
    const photo = ref(null)
    const loading = ref(true)
    const originalUrl = ref(null)
    const previewUrl = ref(null)
    const currentTab = ref('original')
    const previewReady = ref(false)
    const generating = ref(false)
    const exporting = ref(false)
    const customCaption = ref('')
    const includeDate = ref(true)
    const includeLocation = ref(true)
    
    // 裁切参数
    const cropX = ref(0.5)
    const cropY = ref(0.5)
    const cropScale = ref(1.0)
    
    const photoId = parseInt(props.id || route.params.id)
    
    onMounted(async () => {
      try {
        const response = await photoApi.getPhoto(photoId)
        photo.value = response.data
        customCaption.value = response.data.caption || ''
        
        // 立即显示原始照片
        originalUrl.value = `/api/photos/${photoId}/file`
        
        // 后台自动生成预览
        generatePreview()
      } catch (error) {
        console.error('获取照片失败:', error)
      } finally {
        loading.value = false
      }
    })
    
    // 监听设置变化，自动重新生成预览
    watch([customCaption, includeDate, includeLocation], () => {
      if (previewReady.value) {
        generatePreview()
      }
    })
    
    // 裁切参数变化时更新预览
    const onCropChange = () => {
      generatePreview()
    }
    
    const resetCrop = () => {
      cropX.value = 0.5
      cropY.value = 0.5
      generatePreview()
    }
    
    // 裁切预览样式 - 使用 object-fit: cover 让图片填充容器，移动显示不同区域
    const cropPreviewStyle = computed(() => {
      // cropX = 0.5 时，显示中心 → translate(0)
      // cropX = 0 时，显示左边 → 图片向右移 → translate(-50%)
      // cropX = 1 时，显示右边 → 图片向左移 → translate(50%)
      const x = (cropX.value - 0.5) * 100
      const y = (cropY.value - 0.5) * 100
      return {
        transform: `translate(${x}%, ${y}%)`
      }
    })
    
    // 裁切框样式 - 始终在中间，代表最终输出的裁切区域
    const cropBoxStyle = computed(() => {
      // 目标比例是 3:4 (竖版模板)
      const targetRatio = 3 / 4
      const boxWidthPercent = 75
      const boxHeightPercent = boxWidthPercent / targetRatio
      
      // 裁切框始终居中
      const leftPercent = (100 - boxWidthPercent) / 2
      const topPercent = (100 - boxHeightPercent) / 2
      
      return {
        left: `${leftPercent}%`,
        top: `${topPercent}%`,
        width: `${boxWidthPercent}%`,
        height: `${boxHeightPercent}%`
      }
    })
    
    const cropXLabel = computed(() => {
      if (cropX.value < 0.33) return '偏左'
      if (cropX.value > 0.66) return '偏右'
      return '居中'
    })
    
    const cropYLabel = computed(() => {
      if (cropY.value < 0.33) return '偏上'
      if (cropY.value > 0.66) return '偏下'
      return '居中'
    })
    
    const generatePreview = async () => {
      generating.value = true
      previewReady.value = false
      try {
        const response = await exportApi.preview({
          photo_id: photoId,
          template: 'polaroid',
          caption: customCaption.value || null,
          include_date: includeDate.value,
          include_location: includeLocation.value,
          crop_x: cropX.value,
          crop_y: cropY.value,
          crop_scale: cropScale.value
        })
        
        // 创建 blob URL
        const blob = new Blob([response.data], { type: 'image/png' })
        previewUrl.value = URL.createObjectURL(blob)
        previewReady.value = true
        
        // 切换到预览标签
        currentTab.value = 'preview'
      } catch (error) {
        console.error('生成预览失败:', error)
      } finally {
        generating.value = false
      }
    }
    
    const exportPhoto = async () => {
      exporting.value = true
      try {
        const response = await exportApi.exportSingle({
          photo_id: photoId,
          template: 'polaroid',
          caption: customCaption.value || null,
          include_date: includeDate.value,
          include_location: includeLocation.value,
          crop_x: cropX.value,
          crop_y: cropY.value,
          crop_scale: cropScale.value
        })
        
        // 下载文件
        const downloadUrl = response.data.download_url
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = response.data.filename
        link.click()
        
        alert('导出成功！请在下载文件夹中查看')
      } catch (error) {
        console.error('导出失败:', error)
        alert('导出失败，请重试')
      } finally {
        exporting.value = false
      }
    }
    
    const formatDate = (dateStr) => {
      if (!dateStr) return '未知'
      return new Date(dateStr).toLocaleString('zh-CN')
    }
    
    return {
      photo,
      loading,
      originalUrl,
      previewUrl,
      currentTab,
      previewReady,
      generating,
      exporting,
      customCaption,
      includeDate,
      includeLocation,
      cropX,
      cropY,
      cropScale,
      cropPreviewStyle,
      cropBoxStyle,
      cropXLabel,
      cropYLabel,
      onCropChange,
      resetCrop,
      generatePreview,
      exportPhoto,
      formatDate
    }
  }
}
</script>

<style scoped>
.print-view {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
}

.header h1 {
  font-size: 18px;
  font-weight: 600;
}

.content {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.preview-section {
  margin-bottom: 20px;
}

.view-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 8px 8px 0 0;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tab-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.tab-btn:not(.active):hover {
  background: #f5f5f5;
}

.ready-badge {
  display: inline-block;
  width: 16px;
  height: 16px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  font-size: 10px;
  line-height: 16px;
  text-align: center;
  margin-left: 4px;
}

.preview-status {
  margin-top: 8px;
  text-align: center;
}

.preview-status .status {
  font-size: 12px;
  color: #666;
}

.preview-status .status.generating {
  color: #667eea;
}

.preview-status .status.ready {
  color: #10b981;
  font-weight: 500;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

.spinner-small {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.preview-container {
  background: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.preview-placeholder {
  background: white;
  padding: 60px 20px;
  border-radius: 12px;
  text-align: center;
  color: #999;
}

.edit-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card, .edit-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
}

.info-card h3, .edit-card h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.info-card p {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #555;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.form-group .hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox input {
  width: 18px;
  height: 18px;
}

.actions {
  display: flex;
  gap: 12px;
  padding: 0 0 20px;
}

.btn {
  flex: 1;
  padding: 14px 20px;
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

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading, .error {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

/* 裁切相关样式 */
.crop-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
}

.crop-card h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.crop-card .hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
}

.crop-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.crop-control label {
  display: block;
  font-size: 13px;
  color: #555;
  margin-bottom: 8px;
}

.crop-control input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e0e0e0;
  outline: none;
  -webkit-appearance: none;
}

.crop-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
}

.crop-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.btn-small {
  padding: 8px 16px;
  font-size: 13px;
}

/* 裁切预览 */
.crop-preview {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  background: #333;
}

.crop-image {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}

.crop-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.crop-box {
  position: absolute;
  border: 2px dashed #667eea;
  background: rgba(102, 126, 234, 0.1);
  box-sizing: border-box;
}
</style>
