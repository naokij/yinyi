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
        <div class="preview-container" v-if="previewUrl">
          <img :src="previewUrl" alt="打印预览" class="preview-image">
        </div>
        <div v-else class="preview-placeholder">
          <p>点击"生成预览"查看效果</p>
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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { photoApi, exportApi } from '@/api'

export default {
  name: 'Print',
  props: ['id'],
  setup(props) {
    const route = useRoute()
    const photo = ref(null)
    const loading = ref(true)
    const previewUrl = ref(null)
    const generating = ref(false)
    const exporting = ref(false)
    const customCaption = ref('')
    const includeDate = ref(true)
    const includeLocation = ref(true)
    
    const photoId = parseInt(props.id || route.params.id)
    
    onMounted(async () => {
      try {
        const response = await photoApi.getPhoto(photoId)
        photo.value = response.data
        customCaption.value = response.data.caption || ''
      } catch (error) {
        console.error('获取照片失败:', error)
      } finally {
        loading.value = false
      }
    })
    
    const generatePreview = async () => {
      generating.value = true
      try {
        const response = await exportApi.preview({
          photo_id: photoId,
          template: 'polaroid',
          caption: customCaption.value || null,
          include_date: includeDate.value,
          include_location: includeLocation.value
        })
        
        // 创建 blob URL
        const blob = new Blob([response.data], { type: 'image/png' })
        previewUrl.value = URL.createObjectURL(blob)
      } catch (error) {
        console.error('生成预览失败:', error)
        alert('生成预览失败，请重试')
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
          include_location: includeLocation.value
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
      previewUrl,
      generating,
      exporting,
      customCaption,
      includeDate,
      includeLocation,
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
</style>
