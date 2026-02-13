<template>
  <div class="gallery">
    <header class="gallery-header">
      <button class="back-btn" @click="$router.push('/')">←</button>
      <h1>照片库</h1>
        <div class="filter-bar">
          <select v-model="photoStore.filterStatus" @change="applyFilter">
            <option value="">全部</option>
            <option value="analyzed">已分析</option>
            <option value="pending">待处理</option>
            <option value="duplicate">重复</option>
          </select>
          <select v-model="photoStore.sortBy" @change="onSortChange">
            <option value="taken_at">按时间</option>
            <option value="memory_score">按回忆分</option>
            <option value="aesthetic_score">按美观分</option>
          </select>
          <span class="sort-indicator" v-if="photoStore.sortBy !== 'taken_at'">
            {{ sortLabels[photoStore.sortBy] }}
          </span>
        </div>
    </header>
    
    <div class="photo-grid" v-if="photoStore.photos.length > 0">
      <div 
        v-for="photo in photoStore.photos" 
        :key="photo.id"
        class="photo-item"
        :class="{ 'analyzed': photo.status === 'analyzed' }"
        @click="viewPhoto(photo)"
      >
        <div class="photo-thumb">
          <img
            :src="`/api/photos/${photo.id}/file`"
            :alt="photo.filename"
            loading="lazy"
            @error="handleImageError"
          />
          <div class="placeholder" v-if="!photo._imgLoaded">
            <span>{{ photo.filename.slice(0, 2) }}</span>
          </div>
          <div class="status-badge" :class="photo.status">
            {{ statusText[photo.status] }}
          </div>
        </div>
        <div class="photo-info">
          <p class="caption">{{ photo.caption || '暂无文案' }}</p>
          <p class="meta">
            {{ formatDate(photo.taken_at) }}
            <span v-if="photo.memory_score" class="score">
              ⭐ {{ photo.memory_score.toFixed(1) }}
            </span>
          </p>
        </div>
      </div>
    </div>
    
    <div v-else-if="photoStore.loading" class="loading">
      加载中...
    </div>
    
    <div v-else class="empty">
      <p>暂无照片</p>
      <button class="btn btn-primary" @click="$router.push('/')">
        去扫描照片
      </button>
    </div>
    
    <!-- 分页 -->
    <div class="pagination" v-if="photoStore.total > photoStore.pageSize">
      <button 
        :disabled="photoStore.currentPage === 1"
        @click="changePage(photoStore.currentPage - 1)"
      >
        上一页
      </button>
      <span>{{ photoStore.currentPage }} / {{ totalPages }}</span>
      <button 
        :disabled="photoStore.currentPage >= totalPages"
        @click="changePage(photoStore.currentPage + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePhotoStore } from '@/stores/photos'

export default {
  name: 'Gallery',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const photoStore = usePhotoStore()

    const statusText = {
      pending: '待分析',
      analyzing: '分析中',
      analyzed: '已完成',
      duplicate: '重复',
      error: '错误'
    }

    const sortLabels = {
      memory_score: '↓ 回忆分',
      aesthetic_score: '↓ 美观分'
    }

    const totalPages = computed(() =>
      Math.ceil(photoStore.total / photoStore.pageSize)
    )

    onMounted(() => {
      // 检查 URL query 参数
      if (route.query.sort) {
        photoStore.sortBy = route.query.sort
      }
      if (route.query.page) {
        photoStore.currentPage = parseInt(route.query.page)
      }
      photoStore.fetchPhotos()
    })

    const applyFilter = () => {
      photoStore.setFilter(photoStore.filterStatus)
    }

    const changePage = (page) => {
      photoStore.currentPage = page
      photoStore.fetchPhotos()
      // 更新 URL 的 page 参数
      router.push({
        path: '/gallery',
        query: { ...route.query, page: page }
      })
    }

    const onSortChange = () => {
      photoStore.setSort(photoStore.sortBy)
    }

    const viewPhoto = (photo) => {
      router.push(`/print/${photo.id}`)
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '未知日期'
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const handleImageError = (event) => {
      const img = event.target
      const retryCount = parseInt(img.dataset.retryCount || '0')
      
      if (retryCount < 2) {
        // 重试，添加时间戳避免缓存
        img.dataset.retryCount = (retryCount + 1).toString()
        setTimeout(() => {
          img.src = img.src + (img.src.includes('?') ? '&' : '?') + 'retry=' + Date.now()
        }, 500)
      } else {
        // 重试失败，显示占位符
        img.style.display = 'none'
        img.nextElementSibling.style.display = 'flex'
      }
    }

    return {
      photoStore,
      statusText,
      sortLabels,
      totalPages,
      applyFilter,
      changePage,
      onSortChange,
      viewPhoto,
      formatDate,
      handleImageError
    }
  }
}
</script>

<style scoped>
.gallery {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40px;
}

.gallery-header {
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

.gallery-header h1 {
  font-size: 18px;
  font-weight: 600;
  flex: 1;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-bar select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: white;
}

.sort-indicator {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  padding: 16px;
}

.photo-item {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.photo-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.photo-thumb {
  position: relative;
  aspect-ratio: 1;
  background: #f0f0f0;
  overflow: hidden;
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 24px;
}

.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.analyzed {
  background: #d4edda;
  color: #155724;
}

.status-badge.duplicate {
  background: #f8d7da;
  color: #721c24;
}

.photo-info {
  padding: 12px;
}

.caption {
  font-size: 13px;
  line-height: 1.4;
  color: #333;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  font-size: 11px;
  color: #999;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score {
  color: #f59e0b;
  font-weight: 600;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty .btn {
  margin-top: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .photo-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 12px;
  }
}
</style>
